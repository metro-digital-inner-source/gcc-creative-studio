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

import {
  Component,
  OnInit,
  OnDestroy,
  ViewChild,
} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {MatTableDataSource} from '@angular/material/table';
import {MatPaginator, PageEvent} from '@angular/material/paginator';
import {MatSort} from '@angular/material/sort';
import {MatSnackBar} from '@angular/material/snack-bar';
import {Subject, firstValueFrom} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import {MatDialog} from '@angular/material/dialog';

import {AllowlistService, AllowlistEntry} from './allowlist.service';
import {
  handleErrorSnackbar,
  handleSuccessSnackbar,
} from '../../utils/handleMessageSnackbar';
import {ConfirmationDialogComponent} from '../../common/components/confirmation-dialog/confirmation-dialog.component';

@Component({
  selector: 'app-allowlist-management',
  templateUrl: './allowlist-management.component.html',
  styleUrls: ['./allowlist-management.component.scss'],
})
export class AllowlistManagementComponent implements OnInit, OnDestroy {
  displayedColumns: string[] = [
    'type',
    'value',
    'notes',
    'isActive',
    'createdAt',
    'actions',
  ];

  dataSource = new MatTableDataSource<AllowlistEntry>();
  isLoading = false;
  loadError: string | null = null;
  showInactive = false;
  addForm: FormGroup;
  isSubmitting = false;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  private destroy$ = new Subject<void>();

  constructor(
    private allowlistService: AllowlistService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
  ) {
    this.addForm = this.fb.group(
      {
        email: ['', [Validators.email]],
        domain: [''],
        notes: [''],
      },
      {validators: this.atLeastOneValidator},
    );
  }

  ngOnInit(): void {
    this.loadEntries();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  private atLeastOneValidator(group: FormGroup): {[key: string]: boolean} | null {
    const email = group.get('email')?.value?.trim();
    const domain = group.get('domain')?.value?.trim();
    return email || domain ? null : {atLeastOne: true};
  }

  async loadEntries(): Promise<void> {
    this.isLoading = true;
    this.loadError = null;
    try {
      const entries = await firstValueFrom(
        this.allowlistService.list(!this.showInactive),
      );
      this.dataSource.data = entries ?? [];
    } catch (err: any) {
      this.loadError = err?.message ?? 'Failed to load allowlist entries.';
    } finally {
      this.isLoading = false;
    }
  }

  onShowInactiveChange(checked: boolean): void {
    this.showInactive = checked;
    void this.loadEntries();
  }

  applyFilter(event: Event): void {
    const value = (event.target as HTMLInputElement).value.trim().toLowerCase();
    this.dataSource.filter = value;
  }

  async onAdd(): Promise<void> {
    if (this.addForm.invalid) return;
    this.isSubmitting = true;
    const {email, domain, notes} = this.addForm.value;
    const dto: {email?: string; domain?: string; notes?: string} = {notes: notes?.trim() ?? ''};
    if (email?.trim()) dto['email'] = email.trim().toLowerCase();
    if (domain?.trim()) dto['domain'] = domain.trim().toLowerCase();

    try {
      await firstValueFrom(this.allowlistService.create(dto));
      handleSuccessSnackbar(this.snackBar, 'Entry added successfully.');
      this.addForm.reset();
      void this.loadEntries();
    } catch (err) {
      handleErrorSnackbar(this.snackBar, err, 'Add entry');
    } finally {
      this.isSubmitting = false;
    }
  }

  toggleActive(entry: AllowlistEntry): void {
    const action = entry.isActive ? 'Deactivate' : 'Reactivate';
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: `${action} entry?`,
        message: `${action} "${entry.email ?? entry.domain}"?`,
      },
    });
    dialogRef
      .afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe(async confirmed => {
        if (!confirmed) return;
        try {
          await firstValueFrom(
            this.allowlistService.update(entry.id, {isActive: !entry.isActive}),
          );
          handleSuccessSnackbar(this.snackBar, `Entry ${action.toLowerCase()}d.`);
          void this.loadEntries();
        } catch (err) {
          handleErrorSnackbar(this.snackBar, err, action);
        }
      });
  }

  deleteEntry(entry: AllowlistEntry): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: 'Delete entry?',
        message: `Permanently delete "${entry.email ?? entry.domain}"? This cannot be undone.`,
      },
    });
    dialogRef
      .afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe(async confirmed => {
        if (!confirmed) return;
        try {
          await firstValueFrom(this.allowlistService.delete(entry.id));
          handleSuccessSnackbar(this.snackBar, 'Entry deleted.');
          void this.loadEntries();
        } catch (err) {
          handleErrorSnackbar(this.snackBar, err, 'Delete entry');
        }
      });
  }

  entryLabel(entry: AllowlistEntry): string {
    if (entry.email && entry.domain) return `${entry.email} / ${entry.domain}`;
    return entry.email ?? entry.domain ?? '—';
  }

  entryType(entry: AllowlistEntry): string {
    if (entry.email && entry.domain) return 'Email + Domain';
    return entry.email ? 'Email' : 'Domain';
  }

  entryTypeIcon(entry: AllowlistEntry): string {
    if (entry.email && entry.domain) return 'people';
    return entry.email ? 'person' : 'domain';
  }
}
