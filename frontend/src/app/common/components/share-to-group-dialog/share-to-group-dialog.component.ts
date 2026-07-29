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

import {Component, OnInit, Inject} from '@angular/core';
import {MatDialogRef, MAT_DIALOG_DATA} from '@angular/material/dialog';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Group} from '../../models/group.model';
import {GroupService} from '../../../services/group/group.service';

export interface ShareToGroupDialogData {
  mediaItemIds: number[];
}

@Component({
  selector: 'app-share-to-group-dialog',
  template: `
    <h2 mat-dialog-title>Share to Group</h2>
    <mat-dialog-content>
      <p>Select a group to share {{ data.mediaItemIds.length }} item(s) to:</p>

      <div *ngIf="isLoadingGroups" class="loading-container">
        <mat-spinner diameter="40"></mat-spinner>
      </div>

      <form [formGroup]="form" *ngIf="!isLoadingGroups">
        <mat-form-field class="full-width">
          <mat-label>Group</mat-label>
          <mat-select formControlName="groupId" required>
            <mat-option *ngFor="let group of groups" [value]="group.id">
              {{ group.name }}
              <span class="member-count">({{ group.memberCount || 0 }} members)</span>
            </mat-option>
          </mat-select>
          <mat-error *ngIf="form.get('groupId')?.hasError('required')">
            Please select a group
          </mat-error>
        </mat-form-field>
      </form>

      <div *ngIf="!isLoadingGroups && groups.length === 0" class="no-groups">
        <p>You are not a member of any groups yet.</p>
        <p>Contact an administrator to be added to a group.</p>
      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Cancel</button>
      <button
        mat-raised-button
        color="primary"
        (click)="onSubmit()"
        [disabled]="form.invalid || groups.length === 0"
      >
        Share
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
        min-height: 150px;
      }

      .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px;
      }

      .no-groups {
        text-align: center;
        padding: 20px;
        color: rgba(0, 0, 0, 0.54);

        p {
          margin: 8px 0;
        }
      }

      .member-count {
        font-size: 12px;
        color: rgba(0, 0, 0, 0.54);
        margin-left: 8px;
      }
    `,
  ],
})
export class ShareToGroupDialogComponent implements OnInit {
  form: FormGroup;
  groups: Group[] = [];
  isLoadingGroups = true;

  constructor(
    private dialogRef: MatDialogRef<ShareToGroupDialogComponent>,
    private fb: FormBuilder,
    private groupService: GroupService,
    @Inject(MAT_DIALOG_DATA) public data: ShareToGroupDialogData,
  ) {
    this.form = this.fb.group({
      groupId: ['', Validators.required],
    });
  }

  ngOnInit(): void {
    this.loadGroups();
  }

  loadGroups(): void {
    this.groupService.getMyGroups().subscribe({
      next: groups => {
        this.groups = groups;
        this.isLoadingGroups = false;
        // Auto-select if only one group
        if (groups.length === 1) {
          this.form.patchValue({groupId: groups[0].id});
        }
      },
      error: error => {
        console.error('Failed to load groups:', error);
        this.isLoadingGroups = false;
      },
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onSubmit(): void {
    if (this.form.valid) {
      const groupId = this.form.value.groupId;
      this.dialogRef.close({
        groupId,
        mediaItemIds: this.data.mediaItemIds,
      });
    }
  }
}
