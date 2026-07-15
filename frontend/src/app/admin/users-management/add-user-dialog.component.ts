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

import {Component, Inject} from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {Group} from '../../common/models/group.model';

export interface AddUserDialogData {
  groups: Group[];
}

export interface AddUserDialogResult {
  email: string;
  groupId: number;
  role: 'member' | 'admin';
}

@Component({
  selector: 'app-add-user-dialog',
  template: `
    <h2 mat-dialog-title>Add User</h2>

    <form [formGroup]="form" (ngSubmit)="submit()" class="p-4 pt-0">
      <div class="grid gap-4">
        <mat-form-field appearance="outline">
          <mat-label>Email</mat-label>
          <input matInput type="email" formControlName="email" cdkFocusInitial />
          <mat-error *ngIf="form.get('email')?.hasError('required')">
            Email is required
          </mat-error>
          <mat-error *ngIf="form.get('email')?.hasError('email')">
            Enter a valid email
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Group</mat-label>
          <mat-select formControlName="groupId">
            <mat-option *ngFor="let group of data.groups" [value]="group.id">
              {{ group.name }}
            </mat-option>
          </mat-select>
          <mat-error *ngIf="form.get('groupId')?.hasError('required')">
            Group is required
          </mat-error>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Role in Group</mat-label>
          <mat-select formControlName="role">
            <mat-option value="member">Member</mat-option>
            <mat-option value="admin">Admin</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      <div mat-dialog-actions align="end" class="mt-4">
        <button mat-button type="button" (click)="dialogRef.close()">Cancel</button>
        <button mat-flat-button color="primary" type="submit" [disabled]="form.invalid">
          Add User
        </button>
      </div>
    </form>
  `,
})
export class AddUserDialogComponent {
  form;

  constructor(
    private fb: FormBuilder,
    public dialogRef: MatDialogRef<AddUserDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: AddUserDialogData,
  ) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      groupId: [null as number | null, Validators.required],
      role: ['member' as 'member' | 'admin', Validators.required],
    });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const value = this.form.getRawValue();
    this.dialogRef.close({
      email: (value.email || '').trim().toLowerCase(),
      groupId: Number(value.groupId),
      role: value.role || 'member',
    } as AddUserDialogResult);
  }
}
