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
import {MatTableDataSource} from '@angular/material/table';
import {MatSort} from '@angular/material/sort';
import {Subject, firstValueFrom} from 'rxjs';
import {debounceTime, distinctUntilChanged, takeUntil} from 'rxjs/operators';
import {isPlatformBrowser} from '@angular/common';
import {UserService} from './user.service';
import {MatDialog} from '@angular/material/dialog';
import {UserFormComponent} from './user-form.component';
import {MatSnackBar} from '@angular/material/snack-bar';
import {UserModel} from '../../common/models/user.model';
import {Group, GroupMember} from '../../common/models/group.model';
import {GroupService} from '../../services/group/group.service';
import {CreateGroupDialogComponent} from '../groups-management/create-group-dialog/create-group-dialog.component';
import {AddMemberDialogComponent} from '../groups-management/add-member-dialog/add-member-dialog.component';
import {
  AddUserDialogComponent,
  AddUserDialogResult,
} from './add-user-dialog.component';
import {
  handleErrorSnackbar,
  handleSuccessSnackbar,
} from '../../utils/handleMessageSnackbar';
import {ConfirmationDialogComponent} from '../../common/components/confirmation-dialog/confirmation-dialog.component';

// Tree node interface for hierarchical display
interface TreeNode {
  type: 'group' | 'member';
  level: number;
  expandable: boolean;
  isExpanded?: boolean;
  
  // Group properties
  groupId?: number;
  groupName?: string;
  countryCode?: string;
  memberCount?: number;
  
  // Member properties
  member?: GroupMember;
  parentGroupId?: number;
}

@Component({
  selector: 'app-users-management',
  templateUrl: './users-management.component.html',
  styleUrls: ['./users-management.component.scss'],
})
export class UsersManagementComponent implements OnInit, OnDestroy {
  displayedColumns: string[] = [
    'expand',
    'name',
    'email',
    'roles',
    'createdAt',
    'actions',
  ];
  dataSource: MatTableDataSource<TreeNode> = new MatTableDataSource<TreeNode>();
  isLoading = true;
  errorLoadingUsers: string | null = null;
  groups: Group[] = [];
  expandedGroupIds = new Set<number>();
  currentUserId: number | null = null;

  // --- Filtering & Destroy State ---
  private filterSubject = new Subject<string>();
  private destroy$ = new Subject<void>();
  currentFilter = '';
  selectedGroupId: number | null = null;

  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private userService: UserService,
    private groupService: GroupService,
    public dialog: MatDialog,
    private _snackBar: MatSnackBar,
    @Inject(PLATFORM_ID) private platformId: Object,
  ) {}

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      const userDetailsStr = localStorage.getItem('USER_DETAILS');
      if (userDetailsStr) {
        this.currentUserId = JSON.parse(userDetailsStr).id || null;
      }
      this.loadGroups();
    }

    // Debounce filter input
    this.filterSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
      .subscribe(filterValue => {
        this.currentFilter = filterValue;
        this.applyFilterToTree();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadGroups(): void {
    this.isLoading = true;
    this.errorLoadingUsers = null;
    
    this.groupService.getAllGroups().subscribe({
      next: (groups: Group[]) => {
        this.groups = groups;
        this.buildTreeData();
        this.isLoading = false;
      },
      error: (err: any) => {
        this.errorLoadingUsers = 'Failed to load groups and users.';
        console.error('Error loading groups:', err);
        this.isLoading = false;
      },
    });
  }

  buildTreeData(): void {
    const treeNodes: TreeNode[] = [];
    
    for (const group of this.groups) {
      // Add group node
      const groupNode: TreeNode = {
        type: 'group',
        level: 0,
        expandable: true,
        isExpanded: this.expandedGroupIds.has(group.id),
        groupId: group.id,
        groupName: group.name,
        countryCode: group.countryCode,
        memberCount: group.members?.length || 0,
      };
      treeNodes.push(groupNode);
      
      // Add member nodes if group is expanded
      if (this.expandedGroupIds.has(group.id) && group.members) {
        for (const member of group.members) {
          const memberNode: TreeNode = {
            type: 'member',
            level: 1,
            expandable: false,
            member: member,
            parentGroupId: group.id,
          };
          treeNodes.push(memberNode);
        }
      }
    }
    
    this.dataSource.data = treeNodes;
  }

  toggleGroup(groupId: number): void {
    if (this.expandedGroupIds.has(groupId)) {
      this.expandedGroupIds.delete(groupId);
    } else {
      this.expandedGroupIds.add(groupId);
    }
    this.buildTreeData();
  }

  isGroupExpanded(groupId: number): boolean {
    return this.expandedGroupIds.has(groupId);
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.filterSubject.next(filterValue.trim().toLowerCase());
  }

  applyFilterToTree(): void {
    const visibleGroups = this.selectedGroupId
      ? this.groups.filter(group => group.id === this.selectedGroupId)
      : this.groups;

    if (!this.currentFilter) {
      const treeNodes: TreeNode[] = [];
      for (const group of visibleGroups) {
        const groupNode: TreeNode = {
          type: 'group',
          level: 0,
          expandable: true,
          isExpanded: this.expandedGroupIds.has(group.id),
          groupId: group.id,
          groupName: group.name,
          countryCode: group.countryCode,
          memberCount: group.members?.length || 0,
        };
        treeNodes.push(groupNode);

        if (this.expandedGroupIds.has(group.id) && group.members) {
          for (const member of group.members) {
            treeNodes.push({
              type: 'member',
              level: 1,
              expandable: false,
              member,
              parentGroupId: group.id,
            });
          }
        }
      }
      this.dataSource.data = treeNodes;
      return;
    }

    const filter = this.currentFilter.toLowerCase();
    const treeNodes: TreeNode[] = [];

    for (const group of visibleGroups) {
      const matchingMembers = group.members?.filter(member => 
        member.email.toLowerCase().includes(filter) ||
        member.name.toLowerCase().includes(filter)
      ) || [];
      
      // Show group if it has matching members or if group name matches
      if (matchingMembers.length > 0 || group.name.toLowerCase().includes(filter)) {
        const groupNode: TreeNode = {
          type: 'group',
          level: 0,
          expandable: true,
          isExpanded: true, // Auto-expand when filtering
          groupId: group.id,
          groupName: group.name,
          countryCode: group.countryCode,
          memberCount: matchingMembers.length,
        };
        treeNodes.push(groupNode);
        
        // Add matching members
        for (const member of matchingMembers) {
          const memberNode: TreeNode = {
            type: 'member',
            level: 1,
            expandable: false,
            member: member,
            parentGroupId: group.id,
          };
          treeNodes.push(memberNode);
        }
      }
    }
    
    this.dataSource.data = treeNodes;
  }

  applyGroupFilter(groupId: string): void {
    this.selectedGroupId = groupId ? Number(groupId) : null;
    this.applyFilterToTree();
  }

  openUserForm(member: GroupMember): void {
    // Fetch full user details first
    this.userService.getUser(member.userId).subscribe({
      next: (user: UserModel) => {
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
                await firstValueFrom(this.userService.updateUser(result));
                handleSuccessSnackbar(this._snackBar, 'User updated successfully!');
                this.loadGroups();
              } catch (err) {
                console.error('Error updating user:', err);
                handleErrorSnackbar(this._snackBar, err, 'Update user');
              } finally {
                this.isLoading = false;
              }
            }
          });
      },
      error: (err: any) => {
        console.error('Error fetching user:', err);
        handleErrorSnackbar(this._snackBar, err, 'Fetch user');
      },
    });
  }

  deleteUser(userId: number): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: 'Confirm Deletion',
        message: `Are you sure you want to delete user with ID: ${userId}?`,
      },
    });

    dialogRef.afterClosed().subscribe(async (result: any) => {
      if (result) {
        this.isLoading = true;
        try {
          await firstValueFrom(this.userService.deleteUser(userId));
          handleSuccessSnackbar(this._snackBar, 'User deleted successfully!');
          this.loadGroups();
        } catch (err) {
          console.error(`Error deleting user ${userId}:`, err);
          handleErrorSnackbar(this._snackBar, err, 'Delete user');
        } finally {
          this.isLoading = false;
        }
      }
    });
  }

  deleteGroup(groupId: number, groupName: string): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: 'Confirm Group Deletion',
        message: `Are you sure you want to delete the group "${groupName}"? This will remove all group members and cannot be undone.`,
      },
    });

    dialogRef.afterClosed().subscribe(async (result: any) => {
      if (result) {
        this.isLoading = true;
        try {
          await firstValueFrom(this.groupService.deleteGroupAdmin(groupId));
          handleSuccessSnackbar(this._snackBar, `Group "${groupName}" deleted successfully!`);
          // Remove from expanded set if it was expanded
          this.expandedGroupIds.delete(groupId);
          this.loadGroups();
        } catch (err) {
          console.error(`Error deleting group ${groupId}:`, err);
          handleErrorSnackbar(this._snackBar, err, 'Delete group');
        } finally {
          this.isLoading = false;
        }
      }
    });
  }

  openCreateGroupDialog(): void {
    const dialogRef = this.dialog.open(CreateGroupDialogComponent, {
      width: '500px',
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result && result.name) {
        this.isLoading = true;
        
        // Actually create the group via API
        this.groupService.createGroupAdmin(result.name, result.countryCode).subscribe({
          next: (createdGroup: Group) => {
            handleSuccessSnackbar(this._snackBar, `Group "${createdGroup.name}" created successfully!`);
            // Auto-expand the newly created group so admin can add members immediately
            this.expandedGroupIds.add(createdGroup.id);
            this.loadGroups(); // Refresh the tree to show the new group
          },
          error: (err: any) => {
            console.error('Error creating group:', err);
            handleErrorSnackbar(this._snackBar, err, 'Failed to create group');
            this.isLoading = false;
          },
        });
      }
    });
  }

  openAddUserToGroupDialog(member: GroupMember): void {
    // Create a temporary user object for the dialog
    const tempUser: any = {
      id: member.userId,
      email: member.email,
      name: member.name,
    };
    
    const dialogRef = this.dialog.open(AddMemberDialogComponent, {
      width: '500px',
      data: {preselectedUser: tempUser},
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) {
        handleSuccessSnackbar(
          this._snackBar,
          'User added to group successfully!',
        );
        this.loadGroups(); // Refresh the tree
      }
    });
  }

  openAddUserDialog(): void {
    const dialogRef = this.dialog.open(AddUserDialogComponent, {
      width: '500px',
      data: {groups: this.groups},
    });

    dialogRef.afterClosed().subscribe((result: AddUserDialogResult | undefined) => {
      if (result) {
        this.isLoading = true;
        this.groupService
          .addUserToGroupByEmail(result.groupId, result.email)
          .subscribe({
            next: () => {
              handleSuccessSnackbar(this._snackBar, 'User added to group successfully!');
              this.loadGroups();
            },
            error: err => {
              this.isLoading = false;
              handleErrorSnackbar(this._snackBar, err, 'Add user to group');
            },
          });
      }
    });
  }
}
