import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { AiChatbotComponent } from './ai-chatbot.component';

describe('AiChatbotComponent', () => {
  let component: AiChatbotComponent;
  let fixture: ComponentFixture<AiChatbotComponent>;
  let fetchSpy: jasmine.Spy;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiChatbotComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AiChatbotComponent);
    component = fixture.componentInstance;
    fetchSpy = spyOn(window, 'fetch');
    fixture.detectChanges();
  });

  // ==================== Creation ====================

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with chat closed', () => {
    expect(component.isOpen).toBeFalse();
  });

  it('should initialize with empty messages', () => {
    expect(component.messages).toEqual([]);
  });

  it('should initialize with empty userInput', () => {
    expect(component.userInput).toBe('');
  });

  it('should initialize with isLoading false', () => {
    expect(component.isLoading).toBeFalse();
  });

  // ==================== Toggle Chat ====================

  describe('toggleChat', () => {
    it('should open chat when closed', () => {
      component.toggleChat();
      expect(component.isOpen).toBeTrue();
    });

    it('should close chat when open', () => {
      component.isOpen = true;
      component.toggleChat();
      expect(component.isOpen).toBeFalse();
    });

    it('should toggle multiple times', () => {
      component.toggleChat(); // open
      component.toggleChat(); // close
      component.toggleChat(); // open
      expect(component.isOpen).toBeTrue();
    });
  });

  // ==================== Send Message ====================

  describe('sendMessage', () => {
    it('should not send empty message', async () => {
      component.userInput = '';
      await component.sendMessage();

      expect(component.messages.length).toBe(0);
      expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('should not send whitespace-only message', async () => {
      component.userInput = '   ';
      await component.sendMessage();

      expect(component.messages.length).toBe(0);
      expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('should not send when already loading', async () => {
      component.isLoading = true;
      component.userInput = 'Hello';
      await component.sendMessage();

      expect(component.messages.length).toBe(0);
      expect(fetchSpy).not.toHaveBeenCalled();
    });

    it('should add user message to messages array', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: 'Hi there!' }))
      }));

      component.userInput = 'Hello AI';
      await component.sendMessage();

      expect(component.messages.length).toBe(2);
      expect(component.messages[0].role).toBe('user');
      expect(component.messages[0].content).toBe('Hello AI');
    });

    it('should clear userInput after sending', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: 'Response' }))
      }));

      component.userInput = 'Test question';
      await component.sendMessage();

      expect(component.userInput).toBe('');
    });

    it('should set isLoading to true during send', async () => {
      let loadingDuringSend = false;
      fetchSpy.and.callFake(() => {
        loadingDuringSend = component.isLoading;
        return Promise.resolve({
          ok: true,
          text: () => Promise.resolve(JSON.stringify({ respuesta: 'ok' }))
        });
      });

      component.userInput = 'Test';
      await component.sendMessage();

      expect(loadingDuringSend).toBeTrue();
    });

    it('should set isLoading to false after send completes', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: 'done' }))
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      expect(component.isLoading).toBeFalse();
    });

    it('should add assistant message on successful response', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: 'Here is my answer' }))
      }));

      component.userInput = 'What is the price?';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg).toBeTruthy();
      expect(assistantMsg!.content).toBe('Here is my answer');
    });

    it('should handle response with "output" field', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ output: 'Output response' }))
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg!.content).toBe('Output response');
    });

    it('should handle response with "message" field', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ message: 'Message response' }))
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg!.content).toBe('Message response');
    });

    it('should handle empty response text', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve('')
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg).toBeTruthy();
      expect(assistantMsg!.content).toContain('webhook');
    });

    it('should handle empty content in parsed JSON', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: '' }))
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg!.content).toContain('webhook');
    });

    it('should handle HTTP error response', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: false,
        status: 500
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg).toBeTruthy();
      expect(assistantMsg!.content).toContain('error');
    });

    it('should handle network error', async () => {
      fetchSpy.and.returnValue(Promise.reject(new Error('Network failure')));

      component.userInput = 'Test';
      await component.sendMessage();

      expect(component.isLoading).toBeFalse();
      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg!.content).toContain('error');
    });

    it('should handle invalid JSON response', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve('not valid json at all')
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      const assistantMsg = component.messages.find(m => m.role === 'assistant');
      expect(assistantMsg).toBeTruthy();
      // Should show error message
      expect(assistantMsg!.content).toContain('error');
    });

    it('should trim user input before sending', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: 'ok' }))
      }));

      component.userInput = '  Hello  ';
      await component.sendMessage();

      expect(component.messages[0].content).toBe('Hello');
    });

    it('should set timestamp on messages', async () => {
      fetchSpy.and.returnValue(Promise.resolve({
        ok: true,
        text: () => Promise.resolve(JSON.stringify({ respuesta: 'ok' }))
      }));

      component.userInput = 'Test';
      await component.sendMessage();

      expect(component.messages[0].timestamp).toBeInstanceOf(Date);
    });
  });

  // ==================== Clear Chat ====================

  describe('clearChat', () => {
    it('should clear all messages', () => {
      component.messages = [
        { role: 'user', content: 'Hello', timestamp: new Date() },
        { role: 'assistant', content: 'Hi', timestamp: new Date() }
      ];

      component.clearChat();
      expect(component.messages).toEqual([]);
    });

    it('should clear even empty messages array', () => {
      component.clearChat();
      expect(component.messages).toEqual([]);
    });
  });

  // ==================== Key Press Handling ====================

  describe('onKeyPress', () => {
    it('should call sendMessage on Enter key', () => {
      spyOn(component, 'sendMessage');
      const event = new KeyboardEvent('keypress', { key: 'Enter' });
      spyOn(event, 'preventDefault');

      component.onKeyPress(event);

      expect(event.preventDefault).toHaveBeenCalled();
      expect(component.sendMessage).toHaveBeenCalled();
    });

    it('should NOT call sendMessage on Shift+Enter', () => {
      spyOn(component, 'sendMessage');
      const event = new KeyboardEvent('keypress', { key: 'Enter', shiftKey: true });

      component.onKeyPress(event);

      expect(component.sendMessage).not.toHaveBeenCalled();
    });

    it('should NOT call sendMessage on other keys', () => {
      spyOn(component, 'sendMessage');
      const event = new KeyboardEvent('keypress', { key: 'a' });

      component.onKeyPress(event);

      expect(component.sendMessage).not.toHaveBeenCalled();
    });
  });

  // ==================== Ask Example ====================

  describe('askExample', () => {
    it('should set userInput to the example and call sendMessage', () => {
      spyOn(component, 'sendMessage');
      component.askExample('What are the best areas?');

      expect(component.userInput).toBe('What are the best areas?');
      expect(component.sendMessage).toHaveBeenCalled();
    });
  });
});
