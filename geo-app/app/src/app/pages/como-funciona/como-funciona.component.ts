import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-como-funciona',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './como-funciona.component.html',
  styleUrls: ['./como-funciona.component.css'],
})
export class ComoFuncionaComponent {
  currentYear = new Date().getFullYear();
}
