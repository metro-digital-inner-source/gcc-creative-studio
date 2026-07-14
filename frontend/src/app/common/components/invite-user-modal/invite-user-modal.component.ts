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
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {WorkspaceRole} from '../../models/workspace-member.model';
import {Workspace} from '../../models/workspace.model';
import {Group} from '../../models/group.model';
import {WorkspaceService} from '../../../services/workspace/workspace.service';
import {GroupService} from '../../../services/group/group.service';

export interface InviteUserData {
  workspaceName?: string; // For regular mode (workspace-specific invite)
  adminMode?: boolean; // For admin mode (select workspace and group)
}

@Component({
  selector: 'app-invite-user-modal',
  templateUrl: './invite-user-modal.component.html',
})
export class InviteUserModalComponent implements OnInit {
  inviteForm: FormGroup;
  roles = [WorkspaceRole.VIEWER, WorkspaceRole.EDITOR];
  workspaces: Workspace[] = [];
  groups: Group[] = [];
  isLoading = false;

  constructor(
    public dialogRef: MatDialogRef<InviteUserModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: InviteUserData,
    private fb: FormBuilder,
    private workspaceService: WorkspaceService,
    private groupService: GroupService,
  ) {
    // Build form based on mode
    const formConfig: any = {
      email: ['', [Validators.required, Validators.email]],
      role: [WorkspaceRole.EDITOR, Validators.required],
      groupId: ['', Validators.required], // Always required now
    };

    // In admin mode, workspace is also selectable
    if (this.data.adminMode) {
      formConfig.workspaceId = ['', Validators.required];
    }

    this.inviteForm = this.fb.group(formConfig);
  }

  ngOnInit(): void {
    // Load workspaces and groups if in admin mode
    if (this.data.adminMode) {
      this.isLoading = true;
      this.workspaceService.getWorkspaces().subscribe({
        next: (workspaces: Workspace[]) => {
          this.workspaces = workspaces;
        },
        error: (err: any) => {
          console.error('Error loading workspaces:', err);
        },
      });

      this.groupService.getAllGroups().subscribe({
        next: (groups: Group[]) => {
          this.groups = groups;
          this.isLoading = false;
        },
        error: (err: any) => {
          console.error('Error loading groups:', err);
          this.isLoading = false;
        },
      });
    } else {
      // In regular mode, still load groups for selection
      this.groupService.getAllGroups().subscribe({
        next: (groups: Group[]) => {
          this.groups = groups;
        },
        error: (err: any) => {
          console.error('Error loading groups:', err);
        },
      });
    }
  }

  onNoClick(): void {
    this.dialogRef.close();
  }
}
