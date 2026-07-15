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
  GroupUsageBreakdown,
  GroupUsageSummary,
} from '../../common/models/group.model';
import {GroupService} from '../../services/group/group.service';

@Component({
  selector: 'app-admin-group-analytics',
  templateUrl: './admin-group-analytics.component.html',
  styleUrls: ['./admin-group-analytics.component.scss'],
})
export class AdminGroupAnalyticsComponent implements OnInit {
  isLoading = true;
  errorMessage: string | null = null;

  startDate = '';
  endDate = '';
  startCalendarDate: Date | null = null;
  endCalendarDate: Date | null = null;

  summary: GroupUsageSummary = {
    totalGroups: 0,
    totalMembers: 0,
    totalSpendUsd: 0,
    totalTokensConsumed: 0,
  };

  breakdown: GroupUsageBreakdown[] = [];

  constructor(private groupService: GroupService) {}

  ngOnInit(): void {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    this.startCalendarDate = startOfMonth;
    this.endCalendarDate = endOfMonth;

    this.startDate = this.formatDate(startOfMonth);
    this.endDate = this.formatDate(endOfMonth);

    this.loadAnalytics();
  }

  onCalendarDateChange(event: {startDate: Date | null; endDate: Date | null}): void {
    this.startCalendarDate = event.startDate;
    this.endCalendarDate = event.endDate;
    this.startDate = this.formatDate(this.startCalendarDate);
    this.endDate = this.formatDate(this.endCalendarDate);
    this.loadAnalytics();
  }

  private loadAnalytics(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.groupService.getUsageSummary(this.startDate, this.endDate).subscribe({
      next: summary => {
        this.summary = summary;
      },
      error: err => {
        this.errorMessage = err?.message || 'Failed to load usage summary.';
        this.isLoading = false;
      },
    });

    this.groupService.getUsageBreakdown(this.startDate, this.endDate).subscribe({
      next: breakdown => {
        this.breakdown = breakdown;
        this.isLoading = false;
      },
      error: err => {
        this.errorMessage = err?.message || 'Failed to load usage breakdown.';
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
