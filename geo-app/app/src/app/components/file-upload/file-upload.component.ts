// src/app/components/file-upload/file-upload.component.ts - Componente para subir archivos CSV
import { Component, EventEmitter, Output, Input } from '@angular/core'; // decoradores de Angular
import { CommonModule } from '@angular/common'; // módulo común
import { ApiService } from '../../services/api.service'; // servicio API
import { FileValidator } from '../../validators/file-validator'; // validador de archivos

@Component({ // decorador del componente
  selector: 'app-file-upload', // selector HTML
  standalone: true, // componente standalone
  imports: [CommonModule], // importa módulo común
  templateUrl: './file-upload.component.html', // ruta del template
  styleUrls: ['./file-upload.component.css'] // ruta de estilos
})
export class FileUploadComponent { // clase del componente
  @Output() fileUploaded = new EventEmitter<Record<string, unknown>>(); // evento emitido cuando archivo es subido
  @Input() disabled = false; // propiedad de entrada para deshabilitar el componente

  selectedFile: File | null = null; // archivo seleccionado (null si no hay)
  uploading = false; // flag de subida en progreso
  uploadMessage = ''; // mensaje de resultado de subida
  uploadStatus: 'success' | 'error' | '' = ''; // estado de la subida
  uploadProgress = 0; // progreso de subida (0-100)

  constructor(private apiService: ApiService) {} // inyecta servicio API

  // Maneja selección de archivo
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      const validation = FileValidator.validate(file);
      if (validation.valid) {
        this.selectedFile = file;
        this.uploadMessage = `Archivo seleccionado: ${file.name}`;
        this.uploadStatus = '';
      } else {
        this.uploadMessage = validation.errors.join('. ');
        this.uploadStatus = 'error';
        this.selectedFile = null;
      }
    }
  }

  // Sube el archivo seleccionado
  async uploadFile(): Promise<void> { // método asíncrono para subir archivo
    if (!this.selectedFile) { // si no hay archivo seleccionado
      this.uploadMessage = 'Por favor selecciona un archivo primero'; // mensaje de error
      this.uploadStatus = 'error'; // estado error
      return; // sale del método
    }

    this.uploading = true; // activa flag de subida
    this.uploadProgress = 0; // reinicia progreso
    this.uploadMessage = 'Preparando archivo...'; // mensaje de progreso
    this.uploadStatus = ''; // limpia estado

    // Simular progreso visual para archivos grandes
    const progressInterval = setInterval(() => {
      if (this.uploadProgress < 90) {
        this.uploadProgress += 10;
        if (this.uploadProgress < 30) {
          this.uploadMessage = 'Enviando archivo al servidor...';
        } else if (this.uploadProgress < 70) {
          this.uploadMessage = 'Procesando registros...';
        } else {
          this.uploadMessage = 'Validando datos...';
        }
      }
    }, 500);

    try { // bloque try-catch
      const result = await this.apiService.uploadComparablesCsv(this.selectedFile); // llama API para subir
      clearInterval(progressInterval); // detiene progreso simulado
      this.uploadProgress = 100; // completa progreso

      if (result['ok']) { // si respuesta es OK
        this.uploadMessage = `${result['inserted'] || 0} registros insertados correctamente`; // mensaje de éxito
        if ((result['rejects'] as number) > 0) { // si hay rechazos
          this.uploadMessage += ` (${result['rejects']} rechazados por datos incompletos)`; // añade rechazos al mensaje
        }
        this.uploadStatus = 'success'; // estado éxito
        this.fileUploaded.emit(result); // emite evento con resultado
        this.selectedFile = null; // limpia selección
      } else { // si respuesta no es OK
        this.uploadMessage = 'El servidor no pudo procesar el archivo. Verifica que el formato CSV sea correcto y contenga las columnas requeridas.'; // mensaje de error específico
        this.uploadStatus = 'error'; // estado error
      }
    } catch (error: any) { // captura errores
      clearInterval(progressInterval); // detiene progreso simulado
      console.error('Error subiendo archivo:', error); // log del error
      if (error?.status === 413) {
        this.uploadMessage = 'El archivo excede el limite de tamano permitido. Divide el CSV en partes mas pequenas.';
      } else if (error?.status === 0 || error?.message?.includes('network')) {
        this.uploadMessage = 'Error de conexion. Verifica tu conexion a internet e intenta nuevamente.';
      } else {
        this.uploadMessage = 'Error inesperado al subir el archivo. Intenta nuevamente o contacta soporte.';
      }
      this.uploadStatus = 'error'; // estado error
    } finally { // bloque finally
      this.uploading = false; // desactiva flag de subida
    }
  }

  // Limpia la selección de archivo
  clearSelection(): void { // método para limpiar
    this.selectedFile = null; // limpia archivo
    this.uploadMessage = ''; // limpia mensaje
    this.uploadStatus = ''; // limpia estado
  }
}

