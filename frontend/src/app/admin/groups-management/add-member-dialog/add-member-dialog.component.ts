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

import {Component, Inject, OnInit} from '@angular/core';
import {MatDialogRef, MAT_DIALOG_DATA} from '@angular/material/dialog';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Group, GroupMemberRole} from '../../../common/models/group.model';
import {GroupService} from '../../../services/group/group.service';
import {UserModel} from '../../../common/models/user.model';

@Component({
  selector: 'app-add-member-dialog',
  template: `
    <h2 mat-dialog-title>
      {{ data.group ? 'Add Member to ' + data.group.name : 'Add User to Group' }}
    </h2>
    <mat-dialog-content>
      <form [formGroup]="form">
        <mat-form-field *ngIf="!data.group" class="full-width">
          <mat-label>Select Group</mat-label>
          <mat-select formControlName="groupId" required>
            <mat-option *ngFor="let group of groups" [value]="group.id">
              {{ group.name }}
            </mat-option>
          </mat-select>
          <mat-error *ngIf="form.get('groupId')?.hasError('required')">
            Group is required
          </mat-error>
        </mat-form-field>

        <mat-form-field *ngIf="!data.preselectedUser" class="full-width">
          <mat-label>User ID</mat-label>
          <input matInput formControlName="userId" type="number" required />
          <mat-hint>Enter the user's ID</mat-hint>
          <mat-error *ngIf="form.get('userId')?.hasError('required')">
            User ID is required
          </mat-error>
        </mat-form-field>

        <div *ngIf="data.preselectedUser" class="mb-4 p-3 bg-gray-100 rounded">
          <p class="text-sm font-semibold">Selected User:</p>
          <p class="text-sm">{{ data.preselectedUser.name }} ({{ data.preselectedUser.email }})</p>
        </div>

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
        [disabled]="form.invalid || isSubmitting"
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
export class AddMemberDialogComponent implements OnInit {
  form: FormGroup;
  groups: Group[] = [];
  isSubmitting = false;

  constructor(
    private dialogRef: MatDialogRef<AddMemberDialogComponent>,
    private fb: FormBuilder,
    private groupService: GroupService,
    @Inject(MAT_DIALOG_DATA)
    public data: {group?: Group; preselectedUser?: UserModel},
  ) {
    const formConfig: any = {
      role: [GroupMemberRole.MEMBER, Validators.required],
    };

    // If group is not provided, add groupId field
    if (!data.group) {
      formConfig.groupId = ['', Validators.required];
    }

    // If user is not preselected, add userId field
    if (!data.preselectedUser) {
      formConfig.userId = ['', [Validators.required, Validators.min(1)]];
    }

    this.form = this.fb.group(formConfig);
  }

  ngOnInit(): void {
    // Always load groups fresh when dialog opens (even if group is provided)
    // This ensures newly created groups appear in the list
    this.groupService.getAllGroups().subscribe({
      next: groups => {
        this.groups = groups;
      },
      error: err => {
        console.error('Error loading groups:', err);
      },
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    if (this.form.valid && !this.isSubmitting) {
      this.isSubmitting = true;
      const formValue = this.form.value;
      
      const result = {
        groupId: this.data.group?.id || formValue.groupId,
        userId: this.data.preselectedUser?.id || formValue.userId,
        role: formValue.role,
      };

      // Call the API to add user to group
      this.groupService.addUserToGroup(result.groupId, result.userId, result.role).subscribe({
        next: () => {
          this.dialogRef.close(result);
        },
        error: err => {
          console.error('Error adding user to group:', err);
          this.isSubmitting = false;
          // Don't close dialog on error so user can retry
        },
      });
    }
  }
}
