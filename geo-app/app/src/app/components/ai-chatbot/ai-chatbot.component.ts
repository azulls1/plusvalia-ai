import { Component, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InputSanitizer } from '../../validators/input-sanitizer';
import { environment } from '../../../environments/environment';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

@Component({
  selector: 'app-ai-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ai-chatbot.component.html',
  styleUrls: ['./ai-chatbot.component.css']
})
export class AiChatbotComponent {
  @ViewChild('chatMessagesEl') private chatMessagesRef!: ElementRef<HTMLDivElement>;

  // Estado del chat
  isOpen = false;
  isLoading = false;
  userInput = '';
  messages: ChatMessage[] = [];

  // URL del webhook de n8n
  private readonly WEBHOOK_URL = environment.chatWebhookUrl;
  
  constructor() {
    // Chat inicia vacío - las respuestas vendrán del webhook de n8n
  }
  
  // Alternar visibilidad del chat
  toggleChat(): void {
    this.isOpen = !this.isOpen;
  }
  
  // Enviar mensaje
  async sendMessage(): Promise<void> {
    if (!this.userInput.trim() || this.isLoading) {
      return;
    }
    
    // Sanitizar y guardar el mensaje del usuario
    const userMessage = InputSanitizer.sanitize(this.userInput.trim());
    this.messages.push({
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    });
    
    // Limpiar input y mostrar loading
    this.userInput = '';
    this.isLoading = true;
    
    // Scroll al final
    setTimeout(() => this.scrollToBottom(), 100);
    
    try {
      // Llamar al webhook de n8n
      const response = await fetch(this.WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          conversationId: userMessage  // Campo que espera el webhook de n8n
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Obtener el texto de la respuesta primero
      const responseText = await response.text();
      
      // Si la respuesta está vacía, crear un objeto JSON vacío
      if (!responseText || responseText.trim() === '') {
        this.messages.push({
          role: 'assistant',
          content: '⚠️ El webhook respondió pero sin contenido.\n\n' +
                  'Verifica en n8n que:\n' +
                  '1. El nodo "Webhook" esté en modo "Using Respond to Webhook Node"\n' +
                  '2. El nodo "Respond to Webhook" esté conectado y configurado\n' +
                  '3. El workflow esté ACTIVO (no en modo test)',
          timestamp: new Date()
        });
        return; // Salir de la función
      }
      
      // Intentar parsear como JSON
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Error parseando JSON:', parseError);
        console.log('Texto recibido:', responseText);
        throw new Error('La respuesta del servidor no es JSON válido');
      }
      
      // Agregar respuesta del AI
      let responseContent = data.respuesta || data.output || data.message;
      
      // Si la respuesta está vacía, usar mensaje temporal
      if (!responseContent || responseContent.trim() === '') {
        responseContent = '⚠️ El webhook respondió pero sin contenido. Por favor verifica la configuración del nodo "Respond to Webhook" en n8n.\n\n' +
                         'Debe tener:\n' +
                         '- Respond With: JSON\n' +
                         '- Response Body configurado con el campo "respuesta"';
      }
      
      this.messages.push({
        role: 'assistant',
        content: responseContent,
        timestamp: new Date()
      });
      
    } catch (error) {
      console.error('Error al comunicarse con el AI:', error);
      
      // Mensaje de error amigable
      this.messages.push({
        role: 'assistant',
        content: '❌ Lo siento, ocurrió un error al procesar tu consulta. Por favor, verifica la consola del navegador para más detalles.',
        timestamp: new Date()
      });
    } finally {
      this.isLoading = false;
      
      // Scroll al final
      setTimeout(() => this.scrollToBottom(), 100);
    }
  }
  
  // Manejar tecla Enter
  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
  
  // Scroll al final del chat
  private scrollToBottom(): void {
    try {
      const el = this.chatMessagesRef?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    } catch (err) {
      console.error('Error al hacer scroll:', err);
    }
  }

  // TrackBy for messages ngFor
  trackByMessage(index: number, message: ChatMessage): number {
    return index;
  }
  
  // Limpiar conversación
  clearChat(): void {
    this.messages = [];
  }
  
  // Feedback de usuario
  rateFeedback(index: number, rating: 'positive' | 'negative'): void {
    console.log(`[Feedback] Message ${index}: ${rating}`);
    // Track via analytics if available
  }

  // Ejemplos de preguntas
  askExample(example: string): void {
    this.userInput = example;
    this.sendMessage();
  }
}
