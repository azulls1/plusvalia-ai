/**
 * file-validator.ts — Secure File Upload Validation
 *
 * Validates files before upload to prevent:
 *   - Oversized uploads (DoS via large files)
 *   - Incorrect file types (malicious file execution)
 *   - MIME type spoofing (content sniffing attacks)
 *   - Double extensions (e.g., data.csv.exe)
 *
 * OWASP references:
 *   - A04:2021 Insecure Design
 *   - A01:2021 Broken Access Control (unrestricted upload)
 *
 * Usage:
 *   import { FileValidator, FileValidationResult } from '../validators/file-validator';
 *
 *   const result = FileValidator.validate(file);
 *   if (!result.valid) {
 *     console.error(result.errors);
 *   }
 */

/** Result of file validation */
export interface FileValidationResult {
  valid: boolean;
  errors: string[];
}

/** Configuration for allowed file types and limits */
export interface FileValidationConfig {
  maxSizeBytes: number;
  allowedMimeTypes: string[];
  allowedExtensions: string[];
  maxFileNameLength: number;
}

/** Default configuration: CSV files only, 5MB max */
const DEFAULT_CONFIG: FileValidationConfig = {
  maxSizeBytes: 5 * 1024 * 1024,       // 5 MB
  allowedMimeTypes: [
    'text/csv',
    'text/plain',                        // Some systems report CSV as text/plain
    'application/vnd.ms-excel',          // Excel sometimes misidentifies CSV
    'application/csv'
  ],
  allowedExtensions: ['.csv'],
  maxFileNameLength: 255
};

/**
 * CSV magic bytes / BOM signatures that indicate a text-based file.
 * CSV files don't have a universal magic number, but we check for
 * common BOMs and verify the content looks like text.
 */
const TEXT_BOM_SIGNATURES: Uint8Array[] = [
  new Uint8Array([0xEF, 0xBB, 0xBF]),   // UTF-8 BOM
  new Uint8Array([0xFF, 0xFE]),           // UTF-16 LE BOM
  new Uint8Array([0xFE, 0xFF]),           // UTF-16 BE BOM
];

/** Known dangerous file signatures (magic bytes) to reject */
const DANGEROUS_SIGNATURES: { name: string; bytes: number[] }[] = [
  { name: 'EXE/DLL',    bytes: [0x4D, 0x5A] },                          // MZ header
  { name: 'ELF',        bytes: [0x7F, 0x45, 0x4C, 0x46] },             // ELF binary
  { name: 'ZIP/DOCX',   bytes: [0x50, 0x4B, 0x03, 0x04] },             // ZIP archive
  { name: 'RAR',        bytes: [0x52, 0x61, 0x72, 0x21] },             // RAR archive
  { name: 'PDF',        bytes: [0x25, 0x50, 0x44, 0x46] },             // %PDF
  { name: 'GIF',        bytes: [0x47, 0x49, 0x46, 0x38] },             // GIF87a/89a
  { name: 'PNG',        bytes: [0x89, 0x50, 0x4E, 0x47] },             // PNG
  { name: 'JPEG',       bytes: [0xFF, 0xD8, 0xFF] },                    // JPEG
  { name: '7z',         bytes: [0x37, 0x7A, 0xBC, 0xAF] },             // 7-Zip
  { name: 'Mach-O',     bytes: [0xCF, 0xFA, 0xED, 0xFE] },             // macOS binary
];

export class FileValidator {

  /**
   * Validates a file for secure upload.
   * Returns a result with valid=true or a list of error messages.
   */
  static validate(file: File, config: Partial<FileValidationConfig> = {}): FileValidationResult {
    const cfg = { ...DEFAULT_CONFIG, ...config };
    const errors: string[] = [];

    // 1. Check that a file was provided
    if (!file) {
      return { valid: false, errors: ['No se proporcionó ningún archivo.'] };
    }

    // 2. Validate file name length
    if (file.name.length > cfg.maxFileNameLength) {
      errors.push(`El nombre del archivo es demasiado largo (máximo ${cfg.maxFileNameLength} caracteres).`);
    }

    // 3. Validate file name for dangerous patterns
    const nameErrors = FileValidator.validateFileName(file.name);
    errors.push(...nameErrors);

    // 4. Validate file extension
    const extension = FileValidator.getExtension(file.name);
    if (!cfg.allowedExtensions.includes(extension.toLowerCase())) {
      errors.push(
        `Extensión no permitida: "${extension}". Solo se aceptan: ${cfg.allowedExtensions.join(', ')}`
      );
    }

    // 5. Validate MIME type
    if (file.type && !cfg.allowedMimeTypes.includes(file.type.toLowerCase())) {
      errors.push(
        `Tipo MIME no permitido: "${file.type}". Solo se aceptan archivos CSV.`
      );
    }

    // 6. Validate file size
    if (file.size === 0) {
      errors.push('El archivo está vacío.');
    } else if (file.size > cfg.maxSizeBytes) {
      const maxMB = (cfg.maxSizeBytes / (1024 * 1024)).toFixed(1);
      const fileMB = (file.size / (1024 * 1024)).toFixed(1);
      errors.push(`El archivo es demasiado grande (${fileMB} MB). Máximo permitido: ${maxMB} MB.`);
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Performs async content-sniffing validation by reading the first bytes
   * of the file to detect binary/dangerous content disguised as CSV.
   *
   * Call this AFTER the synchronous validate() passes.
   */
  static async validateContent(file: File): Promise<FileValidationResult> {
    const errors: string[] = [];

    try {
      // Read first 8KB to inspect content
      const slice = file.slice(0, 8192);
      const buffer = await slice.arrayBuffer();
      const bytes = new Uint8Array(buffer);

      // Check against dangerous magic bytes
      for (const sig of DANGEROUS_SIGNATURES) {
        if (FileValidator.startsWith(bytes, sig.bytes)) {
          errors.push(
            `El archivo parece ser un binario de tipo "${sig.name}", no un CSV válido.`
          );
          return { valid: false, errors };
        }
      }

      // Verify content looks like text (no null bytes in first 8KB)
      // Null bytes indicate binary content
      for (let i = 0; i < Math.min(bytes.length, 8192); i++) {
        if (bytes[i] === 0x00) {
          // Allow if it's a UTF-16 BOM (which naturally contains null bytes)
          if (i < 2 && (bytes[0] === 0xFF || bytes[0] === 0xFE)) {
            continue;
          }
          errors.push('El archivo contiene datos binarios. Solo se aceptan archivos de texto CSV.');
          return { valid: false, errors };
        }
      }

      // Basic CSV structure check: first line should have commas or semicolons
      const decoder = new TextDecoder('utf-8', { fatal: false });
      const textSample = decoder.decode(bytes.slice(0, 2048));
      const firstLine = textSample.split('\n')[0] || '';

      if (firstLine.length > 0 && !firstLine.includes(',') && !firstLine.includes(';') && !firstLine.includes('\t')) {
        errors.push(
          'El archivo no parece tener formato CSV (no se encontraron separadores de columna en la primera línea).'
        );
      }

    } catch (error) {
      errors.push('No se pudo leer el contenido del archivo para validación.');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Validates the file name for dangerous patterns.
   */
  private static validateFileName(name: string): string[] {
    const errors: string[] = [];

    // Check for null bytes in filename (path traversal technique)
    if (name.includes('\0')) {
      errors.push('El nombre del archivo contiene caracteres inválidos.');
    }

    // Check for path traversal attempts
    if (name.includes('..') || name.includes('/') || name.includes('\\')) {
      errors.push('El nombre del archivo contiene caracteres de navegación no permitidos.');
    }

    // Check for double extensions (e.g., file.csv.exe)
    const parts = name.split('.');
    if (parts.length > 2) {
      const dangerousExts = ['.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.pif', '.js', '.vbs', '.ps1', '.sh'];
      for (const ext of dangerousExts) {
        if (name.toLowerCase().includes(ext)) {
          errors.push(`El nombre del archivo contiene una extensión peligrosa: "${ext}".`);
        }
      }
    }

    // Check for excessively long names that might cause issues
    if (/[<>:"|?*]/.test(name)) {
      errors.push('El nombre del archivo contiene caracteres especiales no permitidos.');
    }

    return errors;
  }

  /**
   * Extracts the file extension including the dot.
   */
  private static getExtension(filename: string): string {
    const lastDot = filename.lastIndexOf('.');
    if (lastDot === -1) return '';
    return filename.substring(lastDot).toLowerCase();
  }

  /**
   * Checks if a byte array starts with the given signature.
   */
  private static startsWith(data: Uint8Array, signature: number[]): boolean {
    if (data.length < signature.length) return false;
    for (let i = 0; i < signature.length; i++) {
      if (data[i] !== signature[i]) return false;
    }
    return true;
  }
}
