/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {Component, OnInit} from '@angular/core';
import {
  AdminDashboardService,
  AdminOverviewStats,
  AdminWorkspaceStats,
  AdminActiveRole,
} from '../../services/admin/admin-dashboard.service';

@Component({
  selector: 'app-analytics-home',
  templateUrl: './analytics-home.component.html',
  styleUrls: ['./analytics-home.component.scss'],
})
export class AnalyticsHomeComponent implements OnInit {
  isLoading = true;
  errorMessage: string | null = null;

  startDate = '';
  endDate = '';
  startCalendarDate: Date | null = null;
  endCalendarDate: Date | null = null;

  overview: AdminOverviewStats | null = null;
  workspaceStats: AdminWorkspaceStats[] = [];
  activeRoles: AdminActiveRole[] = [];

  constructor(private adminService: AdminDashboardService) {}

  ngOnInit(): void {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    this.startCalendarDate = startOfMonth;
    this.endCalendarDate = endOfMonth;
    this.startDate = this.formatDate(startOfMonth);
    this.endDate = this.formatDate(endOfMonth);

    this.loadStats();
  }

  onCalendarDateChange(event: {startDate: Date | null; endDate: Date | null}): void {
    this.startCalendarDate = event.startDate;
    this.endCalendarDate = event.endDate;
    this.startDate = this.formatDate(this.startCalendarDate);
    this.endDate = this.formatDate(this.endCalendarDate);
    this.loadStats();
  }

  private loadStats(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.adminService.getOverviewStats(this.startDate, this.endDate).subscribe({
      next: data => {
        this.overview = data;
      },
      error: err => {
        this.errorMessage = err?.message || 'Failed to load overview statistics.';
        this.isLoading = false;
      },
    });

    this.adminService.getWorkspaceStats(this.startDate, this.endDate).subscribe({
      next: data => {
        this.workspaceStats = data || [];
      },
      error: err => {
        this.errorMessage = err?.message || 'Failed to load workspace statistics.';
        this.isLoading = false;
      },
    });

    this.adminService.getActiveRoles(this.startDate, this.endDate).subscribe({
      next: data => {
        this.activeRoles = data || [];
        this.isLoading = false;
      },
      error: err => {
        this.errorMessage = err?.message || 'Failed to load role distribution.';
        this.isLoading = false;
      },
    });
  }

  private formatDate(date: Date | null): string {
    if (!date) {
      return '';
    }

    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }
}
