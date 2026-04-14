import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-skeleton-loader',
    imports: [CommonModule],
    template: `
    <div class="skeleton-container" [ngStyle]="containerStyle">
      <!-- Card skeleton -->
      <div *ngIf="type === 'card'" class="skeleton-card animate-pulse">
        <div class="skeleton-header"></div>
        <div class="skeleton-line skeleton-line--wide"></div>
        <div class="skeleton-line skeleton-line--medium"></div>
        <div class="skeleton-line skeleton-line--narrow"></div>
      </div>

      <!-- Stat skeleton -->
      <div *ngIf="type === 'stat'" class="skeleton-stat animate-pulse">
        <div class="skeleton-icon"></div>
        <div class="skeleton-line skeleton-line--narrow"></div>
        <div class="skeleton-line skeleton-line--wide"></div>
      </div>

      <!-- List skeleton -->
      <div *ngIf="type === 'list'" class="skeleton-list animate-pulse">
        <div *ngFor="let item of listItems; trackBy: trackByIndex" class="skeleton-list-item">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-list-content">
            <div class="skeleton-line skeleton-line--wide"></div>
            <div class="skeleton-line skeleton-line--medium"></div>
          </div>
        </div>
      </div>

      <!-- Text skeleton -->
      <div *ngIf="type === 'text'" class="skeleton-text animate-pulse">
        <div *ngFor="let line of textLines; trackBy: trackByIndex" class="skeleton-line"
             [ngClass]="'skeleton-line--' + line"></div>
      </div>

      <!-- Map skeleton -->
      <div *ngIf="type === 'map'" class="skeleton-map animate-pulse">
        <div class="skeleton-map-content">
          <svg viewBox="0 0 100 100" class="skeleton-map-icon">
            <circle cx="50" cy="40" r="12" fill="currentColor" opacity="0.2"/>
            <path d="M50 55 L50 75" stroke="currentColor" stroke-width="3" opacity="0.2"/>
            <circle cx="30" cy="65" r="6" fill="currentColor" opacity="0.1"/>
            <circle cx="70" cy="55" r="8" fill="currentColor" opacity="0.1"/>
          </svg>
          <div class="skeleton-line skeleton-line--narrow" style="margin: 0 auto;"></div>
        </div>
      </div>
    </div>
  `,
    styles: [`
    .skeleton-container {
      width: 100%;
    }

    .animate-pulse {
      animation: pulse 1.5s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .skeleton-line {
      height: 12px;
      border-radius: 6px;
      background: linear-gradient(90deg, var(--forest-100, #DFE4E0) 25%, var(--forest-50, #EFF2F0) 50%, var(--forest-100, #DFE4E0) 75%);
      background-size: 400% 100%;
      animation: shimmer 1.5s ease-in-out infinite;
      margin-bottom: 10px;
    }

    @keyframes shimmer {
      0%   { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }

    .skeleton-line--wide   { width: 100%; }
    .skeleton-line--medium { width: 70%; }
    .skeleton-line--narrow { width: 40%; }

    .skeleton-header {
      height: 20px;
      width: 60%;
      border-radius: 6px;
      background: var(--forest-200, #C9D1C8);
      margin-bottom: 16px;
    }

    .skeleton-card {
      padding: 20px;
      border-radius: var(--radius-lg, 12px);
      border: 1px solid var(--color-border-subtle, #EFF2F0);
      background: white;
    }

    .skeleton-stat {
      padding: 16px;
      border-radius: var(--radius-lg, 12px);
      border: 1px solid var(--color-border-subtle, #EFF2F0);
      background: white;
      text-align: center;
    }

    .skeleton-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--forest-100, #DFE4E0);
      margin: 0 auto 12px;
    }

    .skeleton-list-item {
      display: flex;
      gap: 12px;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid var(--color-border-subtle, #EFF2F0);
    }

    .skeleton-list-item:last-child { border-bottom: none; }

    .skeleton-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--forest-100, #DFE4E0);
      flex-shrink: 0;
    }

    .skeleton-list-content {
      flex: 1;
    }

    .skeleton-map {
      height: 200px;
      border-radius: var(--radius-lg, 12px);
      background: var(--forest-50, #EFF2F0);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .skeleton-map-content {
      text-align: center;
      color: var(--forest-300, #9EADA3);
    }

    .skeleton-map-icon {
      width: 60px;
      height: 60px;
      margin-bottom: 8px;
    }
  `]
})
export class SkeletonLoaderComponent {
  @Input() type: 'card' | 'stat' | 'list' | 'text' | 'map' = 'card';
  @Input() count = 3;
  @Input() containerStyle: Record<string, string> = {};

  get listItems(): number[] {
    return Array.from({ length: this.count }, (_, i) => i);
  }

  get textLines(): string[] {
    return ['wide', 'medium', 'wide', 'narrow'];
  }

  trackByIndex(index: number): number {
    return index;
  }
}
