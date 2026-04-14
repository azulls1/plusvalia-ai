/**
 * input-sanitizer.ts — Input Sanitization Utilities
 *
 * Provides defense-in-depth sanitization for user inputs:
 *   1. XSS prevention (strip HTML tags and dangerous attributes)
 *   2. SQL injection prevention (escape/detect SQL patterns)
 *   3. Max length validation
 *   4. Unicode normalization (NFC form)
 *
 * OWASP references:
 *   - A03:2021 Injection (SQL, XSS, command injection)
 *   - A07:2021 Cross-Site Scripting (XSS)
 *
 * Usage:
 *   import { InputSanitizer } from '../validators/input-sanitizer';
 *
 *   const safe = InputSanitizer.sanitize(userInput);
 *   const result = InputSanitizer.validate(userInput, { maxLength: 200 });
 */

/** Result of input validation */
export interface InputValidationResult {
  valid: boolean;
  sanitized: string;
  errors: string[];
  warnings: string[];
}

/** Configuration for input validation */
export interface InputValidationConfig {
  maxLength: number;
  minLength: number;
  allowHtml: boolean;
  allowNumbers: boolean;
  allowSpecialChars: boolean;
  trimWhitespace: boolean;
  normalizeUnicode: boolean;
  checkSqlInjection: boolean;
  checkXss: boolean;
  customPattern?: RegExp;
  customPatternMessage?: string;
}

/** Default configuration */
const DEFAULT_CONFIG: InputValidationConfig = {
  maxLength: 1000,
  minLength: 0,
  allowHtml: false,
  allowNumbers: true,
  allowSpecialChars: true,
  trimWhitespace: true,
  normalizeUnicode: true,
  checkSqlInjection: true,
  checkXss: true
};

/**
 * Patterns that indicate potential SQL injection attempts.
 * These are checked case-insensitively against the input.
 */
const SQL_INJECTION_PATTERNS: RegExp[] = [
  /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b\s)/i,
  /(\b(OR|AND)\b\s+\d+\s*=\s*\d+)/i,         // OR 1=1, AND 1=1
  /(--|#|\/\*|\*\/)/,                           // SQL comments
  /(\b(WAITFOR|BENCHMARK|SLEEP)\b\s*\()/i,     // Time-based injection
  /(\bINTO\s+(OUT|DUMP)FILE\b)/i,              // File operations
  /(\bLOAD_FILE\s*\()/i,                       // File read
  /(;\s*(DROP|DELETE|UPDATE|INSERT)\b)/i,       // Stacked queries
  /(\bCAST\s*\(.*\bAS\b)/i,                    // CAST injection
  /(\bCONVERT\s*\()/i,                         // CONVERT injection
  /(0x[0-9a-fA-F]+)/,                          // Hex encoding
  /(\bCHAR\s*\(\d+\))/i,                       // CHAR() encoding
];

/**
 * Patterns that indicate potential XSS attacks.
 */
const XSS_PATTERNS: RegExp[] = [
  /<script\b[^>]*>/i,                          // Script tags
  /javascript\s*:/i,                           // javascript: protocol
  /on\w+\s*=/i,                                // Event handlers (onclick, onerror, etc.)
  /(<\s*\/?\s*)(iframe|object|embed|form|input|button|textarea|select|link|meta|base|applet)/i,
  /expression\s*\(/i,                          // CSS expression()
  /url\s*\(\s*(javascript|data)\s*:/i,         // CSS url() with dangerous protocol
  /data\s*:\s*text\/html/i,                    // Data URI with HTML
  /vbscript\s*:/i,                             // VBScript protocol
  /<!\[CDATA\[/i,                              // CDATA sections
  /<!--.*-->/,                                 // HTML comments (can hide payloads)
  /&\{/,                                       // HTML entity injection
];

export class InputSanitizer {

  /**
   * Quick sanitization — strips dangerous content and returns clean string.
   * Use this for simple cases where you just need a safe string.
   */
  static sanitize(input: string, maxLength: number = 1000): string {
    if (typeof input !== 'string') return '';

    let sanitized = input;

    // 1. Normalize Unicode to NFC (canonical decomposition + composition)
    sanitized = sanitized.normalize('NFC');

    // 2. Trim whitespace
    sanitized = sanitized.trim();

    // 3. Remove null bytes
    sanitized = sanitized.replace(/\0/g, '');

    // 4. Strip HTML tags
    sanitized = InputSanitizer.stripHtmlTags(sanitized);

    // 5. Encode HTML entities for remaining special chars
    sanitized = InputSanitizer.encodeHtmlEntities(sanitized);

    // 6. Truncate to max length
    if (sanitized.length > maxLength) {
      sanitized = sanitized.substring(0, maxLength);
    }

    return sanitized;
  }

  /**
   * Full validation — checks input against all security rules.
   * Returns validation result with sanitized string and any errors/warnings.
   */
  static validate(
    input: string,
    config: Partial<InputValidationConfig> = {}
  ): InputValidationResult {
    const cfg = { ...DEFAULT_CONFIG, ...config };
    const errors: string[] = [];
    const warnings: string[] = [];

    // Handle non-string input
    if (typeof input !== 'string') {
      return {
        valid: false,
        sanitized: '',
        errors: ['El valor proporcionado no es texto válido.'],
        warnings: []
      };
    }

    let sanitized = input;

    // Step 1: Unicode normalization
    if (cfg.normalizeUnicode) {
      sanitized = sanitized.normalize('NFC');
    }

    // Step 2: Trim whitespace
    if (cfg.trimWhitespace) {
      sanitized = sanitized.trim();
    }

    // Step 3: Remove null bytes (always — these are never valid in user input)
    sanitized = sanitized.replace(/\0/g, '');

    // Step 4: Check min length
    if (sanitized.length < cfg.minLength) {
      errors.push(`El texto es demasiado corto (mínimo ${cfg.minLength} caracteres).`);
    }

    // Step 5: Check max length
    if (sanitized.length > cfg.maxLength) {
      warnings.push(`El texto excede el máximo de ${cfg.maxLength} caracteres y será truncado.`);
      sanitized = sanitized.substring(0, cfg.maxLength);
    }

    // Step 6: Check for SQL injection patterns
    if (cfg.checkSqlInjection) {
      const sqlResult = InputSanitizer.detectSqlInjection(sanitized);
      if (sqlResult.detected) {
        warnings.push(`Se detectó un patrón potencialmente peligroso: "${sqlResult.pattern}". La entrada fue sanitizada.`);
        // Don't block, but sanitize the dangerous parts
        sanitized = InputSanitizer.neutralizeSqlPatterns(sanitized);
      }
    }

    // Step 7: Check for XSS patterns
    if (cfg.checkXss) {
      const xssResult = InputSanitizer.detectXss(sanitized);
      if (xssResult.detected) {
        warnings.push('Se detectó contenido HTML/script potencialmente peligroso. El contenido fue sanitizado.');
        sanitized = InputSanitizer.stripHtmlTags(sanitized);
        sanitized = InputSanitizer.encodeHtmlEntities(sanitized);
      }
    }

    // Step 8: Strip HTML if not allowed
    if (!cfg.allowHtml) {
      sanitized = InputSanitizer.stripHtmlTags(sanitized);
    }

    // Step 9: Custom pattern validation
    if (cfg.customPattern && !cfg.customPattern.test(sanitized)) {
      errors.push(cfg.customPatternMessage || 'El formato del texto no es válido.');
    }

    return {
      valid: errors.length === 0,
      sanitized,
      errors,
      warnings
    };
  }

  /**
   * Sanitizes a value specifically for use in URL query parameters.
   */
  static sanitizeForUrl(input: string, maxLength: number = 200): string {
    let sanitized = InputSanitizer.sanitize(input, maxLength);
    // Double-encode to prevent parameter pollution
    return encodeURIComponent(sanitized);
  }

  /**
   * Sanitizes a numeric input, returning NaN for invalid values.
   */
  static sanitizeNumber(input: unknown, min?: number, max?: number): number {
    const num = typeof input === 'number' ? input : parseFloat(String(input));

    if (isNaN(num) || !isFinite(num)) return NaN;
    if (min !== undefined && num < min) return min;
    if (max !== undefined && num > max) return max;

    return num;
  }

  /**
   * Sanitizes coordinates (lat/lon) with geographic bounds checking.
   */
  static sanitizeCoordinate(lat: unknown, lon: unknown): { lat: number; lon: number } | null {
    const safeLat = InputSanitizer.sanitizeNumber(lat, -90, 90);
    const safeLon = InputSanitizer.sanitizeNumber(lon, -180, 180);

    if (isNaN(safeLat) || isNaN(safeLon)) return null;

    return { lat: safeLat, lon: safeLon };
  }

  // ==================== Private Helper Methods ====================

  /**
   * Strips all HTML tags from a string.
   */
  private static stripHtmlTags(input: string): string {
    // First pass: remove tags
    let result = input.replace(/<[^>]*>/g, '');
    // Second pass: remove any remaining angle brackets
    result = result.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return result;
  }

  /**
   * Encodes HTML special characters to prevent XSS.
   */
  private static encodeHtmlEntities(input: string): string {
    return input
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  }

  /**
   * Detects SQL injection patterns in the input.
   */
  private static detectSqlInjection(input: string): { detected: boolean; pattern: string } {
    for (const pattern of SQL_INJECTION_PATTERNS) {
      if (pattern.test(input)) {
        return { detected: true, pattern: pattern.source.substring(0, 30) + '...' };
      }
    }
    return { detected: false, pattern: '' };
  }

  /**
   * Detects XSS patterns in the input.
   */
  private static detectXss(input: string): { detected: boolean } {
    for (const pattern of XSS_PATTERNS) {
      if (pattern.test(input)) {
        return { detected: true };
      }
    }
    return { detected: false };
  }

  /**
   * Neutralizes SQL-dangerous characters by escaping them.
   * This is defense-in-depth — the backend should ALSO use parameterized queries.
   */
  private static neutralizeSqlPatterns(input: string): string {
    return input
      .replace(/'/g, "''")        // Escape single quotes
      .replace(/;/g, '')          // Remove semicolons
      .replace(/--/g, '')         // Remove SQL comments
      .replace(/\/\*/g, '')       // Remove block comment start
      .replace(/\*\//g, '');      // Remove block comment end
  }
}
