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
import {MatDialogRef, MAT_DIALOG_DATA} from '@angular/material/dialog';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Group, GroupMemberRole} from '../../../common/models/group.model';

@Component({
  selector: 'app-add-member-dialog',
  template: `
    <h2 mat-dialog-title>Add Member to {{ data.group.name }}</h2>
    <mat-dialog-content>
      <form [formGroup]="form">
        <mat-form-field class="full-width">
          <mat-label>User ID</mat-label>
          <input matInput formControlName="userId" type="number" required />
          <mat-hint>Enter the user's ID</mat-hint>
          <mat-error *ngIf="form.get('userId')?.hasError('required')">
            User ID is required
          </mat-error>
        </mat-form-field>

        <mat-form-field class="full-width">
          <mat-label>Role</mat-label>
          <mat-select formControlName="role" required>
            <mat-option value="member">Member</mat-option>
            <mat-option value="admin">Admin</mat-option>
          </mat-select>
          <mat-error *ngIf="form.get('role')?.hasError('required')">
            Role is required
          </mat-error>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Cancel</button>
      <button
        mat-raised-button
        color="primary"
        (click)="onSubmit()"
        [disabled]="form.invalid"
      >
        Add Member
      </button>
    </mat-dialog-actions>
  `,
  styles: [
    `
      .full-width {
        width: 100%;
        margin-bottom: 16px;
      }

      mat-dialog-content {
        min-width: 400px;
      }
    `,
  ],
})
export class AddMemberDialogComponent {
  form: FormGroup;

  constructor(
    private dialogRef: MatDialogRef<AddMemberDialogComponent>,
    private fb: FormBuilder,
    @Inject(MAT_DIALOG_DATA) public data: {group: Group},
  ) {
    this.form = this.fb.group({
      userId: ['', [Validators.required, Validators.min(1)]],
      role: [GroupMemberRole.MEMBER, Validators.required],
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    if (this.form.valid) {
      this.dialogRef.close(this.form.value);
    }
  }
}
