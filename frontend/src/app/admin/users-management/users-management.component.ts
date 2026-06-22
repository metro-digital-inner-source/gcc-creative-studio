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
  Inject,
  PLATFORM_ID,
} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {MatTableDataSource} from '@angular/material/table';
import {MatPaginator, PageEvent} from '@angular/material/paginator';
import {MatSort} from '@angular/material/sort';
import {Subject, firstValueFrom} from 'rxjs';
import {debounceTime, distinctUntilChanged, takeUntil} from 'rxjs/operators';
import {isPlatformBrowser} from '@angular/common';
import {UserService, PaginatedResponse} from './user.service';
import {MatDialog} from '@angular/material/dialog';
import {UserFormComponent} from './user-form.component';
import {MatSnackBar} from '@angular/material/snack-bar';
import {UserModel, UserRolesEnum} from '../../common/models/user.model';
import {
  AllowlistEntry,
  AllowlistService,
} from '../allowlist-management/allowlist.service';
import {
  handleErrorSnackbar,
  handleSuccessSnackbar,
} from '../../utils/handleMessageSnackbar';
import {ConfirmationDialogComponent} from '../../common/components/confirmation-dialog/confirmation-dialog.component';

@Component({
  selector: 'app-users-management',
  templateUrl: './users-management.component.html',
  styleUrls: ['./users-management.component.scss'],
})
export class UsersManagementComponent implements OnInit, OnDestroy {
  accessColumns: string[] = [
    'type',
    'value',
    'notes',
    'status',
    'added',
    'accessActions',
  ];
  displayedColumns: string[] = [
    'picture',
    'name',
    'email',
    'roles',
    'createdAt',
    'updatedAt',
    'actions',
  ];
  dataSource: MatTableDataSource<UserModel> =
    new MatTableDataSource<UserModel>();
  accessEntries: AllowlistEntry[] = [];
  isLoading = true;
  isAccessLoading = false;
  isAccessSubmitting = false;
  errorLoadingUsers: string | null = null;
  errorLoadingAccess: string | null = null;
  lastResponse: PaginatedResponse | undefined;
  accessForm: FormGroup;

  // --- Pagination State ---
  totalUsers = 0;
  limit = 10;
  currentPageIndex = 0;
  currentUserId: number | null = null;

  // --- Filtering & Destroy State ---
  private filterSubject = new Subject<string>();
  private destroy$ = new Subject<void>();
  currentFilter = '';
  includeDeleted = false; // Added

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private userService: UserService,
    private allowlistService: AllowlistService,
    private fb: FormBuilder,
    public dialog: MatDialog,
    private _snackBar: MatSnackBar,
    @Inject(PLATFORM_ID) private platformId: Object,
  ) {
    this.accessForm = this.fb.group(
      {
        email: ['', [Validators.email]],
        domain: [''],
        notes: [''],
      },
      {validators: this.atLeastOneValidator},
    );
  }

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      const userDetailsStr = localStorage.getItem('USER_DETAILS');
      if (userDetailsStr) {
        this.currentUserId = JSON.parse(userDetailsStr).id || null;
      }
      void this.fetchPage(0);
      void this.loadAccessEntries();
    }

    // Debounce filter input to avoid excessive Firestore reads
    this.filterSubject
      .pipe(debounceTime(500), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe(filterValue => {
        this.currentFilter = filterValue;
        this.resetPaginationAndFetch();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  handlePageEvent(event: PageEvent) {
    // If page size changes, we must reset everything.
    if (this.limit !== event.pageSize) {
      this.limit = event.pageSize;
      this.resetPaginationAndFetch();
      return;
    }
    void this.fetchPage(event.pageIndex);
  }

  private atLeastOneValidator(group: FormGroup): {[key: string]: boolean} | null {
    const email = group.get('email')?.value?.trim();
    const domain = group.get('domain')?.value?.trim();
    return email || domain ? null : {atLeastOne: true};
  }

  async fetchPage(targetPageIndex: number) {
    this.isLoading = true;
    const offset = targetPageIndex * this.limit;

    try {
      const finalResponse = await firstValueFrom(
        this.userService.getUsers(
          this.limit,
          this.currentFilter,
          offset,
          this.includeDeleted, // Pass here
        ),
        {defaultValue: {data: [], count: 0} as any},
      );

      this.dataSource.data = finalResponse.data;
      this.totalUsers = finalResponse.count;
      this.currentPageIndex = targetPageIndex;
    } catch (err) {
      this.errorLoadingUsers = 'Failed to load users.';
      console.error(err);
    } finally {
      this.isLoading = false;
    }
  }

  async loadAccessEntries(): Promise<void> {
    this.isAccessLoading = true;
    this.errorLoadingAccess = null;

    try {
      this.accessEntries = await firstValueFrom(
        this.allowlistService.list(false),
        {defaultValue: []},
      );
    } catch (err) {
      this.errorLoadingAccess = 'Failed to load access list.';
      console.error(err);
    } finally {
      this.isAccessLoading = false;
    }
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.filterSubject.next(filterValue.trim().toLowerCase());
  }

  private resetPaginationAndFetch() {
    this.currentPageIndex = 0;
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    void this.fetchPage(0);
  }

  onIncludeDeletedChange(checked: boolean) {
    this.includeDeleted = checked;
    this.resetPaginationAndFetch();
  }

  async onAddAccess(): Promise<void> {
    if (this.accessForm.invalid) return;

    this.isAccessSubmitting = true;
    const {email, domain, notes} = this.accessForm.value;
    const dto: {email?: string; domain?: string; notes?: string} = {
      notes: notes?.trim() ?? '',
    };

    if (email?.trim()) dto.email = email.trim().toLowerCase();
    if (domain?.trim()) dto.domain = domain.trim().toLowerCase();

    try {
      await firstValueFrom(this.allowlistService.create(dto));
      handleSuccessSnackbar(this._snackBar, 'Access entry added successfully.');
      this.accessForm.reset();
      await this.loadAccessEntries();
    } catch (err) {
      handleErrorSnackbar(this._snackBar, err, 'Add access entry');
    } finally {
      this.isAccessSubmitting = false;
    }
  }

  toggleAccessEntry(entry: AllowlistEntry): void {
    const action = entry.isActive ? 'Deactivate' : 'Reactivate';
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: `${action} access entry?`,
        message: `${action} "${this.entryLabel(entry)}"?`,
      },
    });

    dialogRef.afterClosed().subscribe(async result => {
      if (!result) return;

      try {
        await firstValueFrom(
          this.allowlistService.update(entry.id, {isActive: !entry.isActive}),
        );
        handleSuccessSnackbar(
          this._snackBar,
          `Access entry ${action.toLowerCase()}d successfully!`,
        );
        await this.loadAccessEntries();
      } catch (err) {
        handleErrorSnackbar(this._snackBar, err, action);
      }
    });
  }

  deleteAccessEntry(entry: AllowlistEntry): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: 'Delete access entry?',
        message: `Permanently delete "${this.entryLabel(entry)}"?`,
      },
    });

    dialogRef.afterClosed().subscribe(async result => {
      if (!result) return;

      try {
        await firstValueFrom(this.allowlistService.delete(entry.id));
        handleSuccessSnackbar(this._snackBar, 'Access entry deleted successfully!');
        await this.loadAccessEntries();
      } catch (err) {
        handleErrorSnackbar(this._snackBar, err, 'Delete access entry');
      }
    });
  }

  async restoreUser(userId: string): Promise<void> {
    this.isLoading = true;
    try {
      await firstValueFrom(this.userService.restoreUser(userId));
      handleSuccessSnackbar(this._snackBar, 'User restored successfully!');
      await this.fetchPage(this.currentPageIndex);
    } catch (err) {
      console.error(`Error restoring user ${userId}:`, err);
      handleErrorSnackbar(this._snackBar, err, 'Restore user');
    } finally {
      this.isLoading = false;
    }
  }

  openUserForm(user: UserModel): void {
    const dialogRef = this.dialog.open(UserFormComponent, {
      width: '450px',
      data: {user: user, isEditMode: true},
    });

    dialogRef
      .afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe(async (result: UserModel | undefined) => {
        if (result) {
          this.isLoading = true;
          try {
            // The form returns the full user object with updated roles
            await firstValueFrom(this.userService.updateUser(result));
            handleSuccessSnackbar(this._snackBar, 'User updated successfully!');
            // Refetch to show updated data on the current page.
            await this.fetchPage(this.currentPageIndex);
          } catch (err) {
            console.error(`Error updating user ${result.id}:`, err);
            handleErrorSnackbar(this._snackBar, err, 'Update user');
          } finally {
            this.isLoading = false;
          }
        }
      });
  }

  deleteUser(userId: string): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: 'Confirm Deletion',
        message: `Are you sure you want to delete user with ID: ${userId}?`,
      },
    });

    dialogRef.afterClosed().subscribe(async result => {
      if (result) {
        this.isLoading = true;
        try {
          await firstValueFrom(this.userService.deleteUser(userId));
          handleSuccessSnackbar(this._snackBar, 'User deleted successfully!');
          this.resetPaginationAndFetch();
        } catch (err) {
          console.error(`Error deleting user ${userId}:`, err);
          handleErrorSnackbar(this._snackBar, err, 'Delete user');
        } finally {
          this.isLoading = false;
        }
      }
    });
  }

  public getRoleChipClass(role: string): string {
    const roleLower = role.toLowerCase();

    // Using a switch statement makes it easy to add more roles later
    switch (roleLower) {
      case UserRolesEnum.ADMIN.toLowerCase():
        return '!bg-amber-500/20 !text-amber-300';
      case UserRolesEnum.USER.toLowerCase():
        return '!bg-blue-500/20 !text-blue-300';
      case UserRolesEnum.CREATOR.toLowerCase():
        return '!bg-purple-500/20 !text-purple-300';
      case UserRolesEnum.WORKFLOWS.toLowerCase():
        return '!bg-green-500/20 !text-green-300';
      default:
        // It's good practice to have a default style
        return '!bg-gray-500/20 !text-gray-300';
    }
  }

  entryLabel(entry: AllowlistEntry): string {
    if (entry.email && entry.domain) return `${entry.email} / ${entry.domain}`;
    return entry.email ?? entry.domain ?? '—';
  }

  entryType(entry: AllowlistEntry): string {
    if (entry.email && entry.domain) return 'Email + Domain';
    return entry.email ? 'Email' : 'Domain';
  }
}
