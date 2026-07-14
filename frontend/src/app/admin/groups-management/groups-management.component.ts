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

import {Component, OnInit, ViewChild} from '@angular/core';
import {MatTableDataSource} from '@angular/material/table';
import {MatPaginator} from '@angular/material/paginator';
import {MatSort} from '@angular/material/sort';
import {MatDialog} from '@angular/material/dialog';
import {MatSnackBar} from '@angular/material/snack-bar';
import {GroupService} from '../../services/group/group.service';
import {
  Group,
  GroupUsageBreakdown,
  GroupUsageSummary,
} from '../../common/models/group.model';
import {CreateGroupDialogComponent} from './create-group-dialog/create-group-dialog.component';
import {AddMemberDialogComponent} from './add-member-dialog/add-member-dialog.component';
import {
  handleErrorSnackbar,
  handleSuccessSnackbar,
} from '../../utils/handleMessageSnackbar';

@Component({
  selector: 'app-groups-management',
  templateUrl: './groups-management.component.html',
  styleUrls: ['./groups-management.component.scss'],
})
export class GroupsManagementComponent implements OnInit {
  // Groups table
  displayedColumns: string[] = [
    'id',
    'name',
    'countryCode',
    'memberCount',
    'createdAt',
    'actions',
  ];
  dataSource: MatTableDataSource<Group> = new MatTableDataSource<Group>();
  isLoadingGroups = true;

  // Usage breakdown table
  usageColumns: string[] = [
    'groupName',
    'countryCode',
    'memberCount',
    'spendUsd',
    'tokensConsumed',
    'activityCount',
  ];
  usageDataSource: MatTableDataSource<GroupUsageBreakdown> =
    new MatTableDataSource<GroupUsageBreakdown>();
  isLoadingUsage = true;

  // Usage summary
  usageSummary: GroupUsageSummary | null = null;

  @ViewChild('groupsPaginator') groupsPaginator!: MatPaginator;
  @ViewChild('groupsSort') groupsSort!: MatSort;
  @ViewChild('usagePaginator') usagePaginator!: MatPaginator;
  @ViewChild('usageSort') usageSort!: MatSort;

  constructor(
    private groupService: GroupService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.loadGroups();
    this.loadUsageData();
  }

  loadGroups(): void {
    this.isLoadingGroups = true;
    this.groupService.getAllGroups().subscribe({
      next: groups => {
        // Calculate member count from members array
        const groupsWithCount = groups.map(g => ({
          ...g,
          memberCount: g.members?.length || 0,
        }));
        this.dataSource.data = groupsWithCount;
        this.dataSource.paginator = this.groupsPaginator;
        this.dataSource.sort = this.groupsSort;
        this.isLoadingGroups = false;
      },
      error: error => {
        handleErrorSnackbar(
          this.snackBar,
          error,
          'Failed to load groups',
        );
        this.isLoadingGroups = false;
      },
    });
  }

  loadUsageData(): void {
    this.isLoadingUsage = true;
    // Load summary
    this.groupService.getUsageSummary().subscribe({
      next: summary => {
        this.usageSummary = summary;
      },
      error: error => {
        handleErrorSnackbar(
          this.snackBar,
          error,
          'Failed to load usage summary',
        );
      },
    });

    // Load breakdown
    this.groupService.getUsageBreakdown().subscribe({
      next: breakdown => {
        this.usageDataSource.data = breakdown;
        this.usageDataSource.paginator = this.usagePaginator;
        this.usageDataSource.sort = this.usageSort;
        this.isLoadingUsage = false;
      },
      error: error => {
        handleErrorSnackbar(
          this.snackBar,
          error,
          'Failed to load usage breakdown',
        );
        this.isLoadingUsage = false;
      },
    });
  }

  openCreateGroupDialog(): void {
    const dialogRef = this.dialog.open(CreateGroupDialogComponent, {
      width: '500px',
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.createGroup(result.name, result.countryCode);
      }
    });
  }

  createGroup(name: string, countryCode?: string): void {
    this.groupService.createGroupAdmin(name, countryCode).subscribe({
      next: group => {
        handleSuccessSnackbar(this.snackBar, 'Group created successfully');
        this.loadGroups();
      },
      error: error => {
        handleErrorSnackbar(this.snackBar, error, 'Failed to create group');
      },
    });
  }

  openAddMemberDialog(group: Group): void {
    const dialogRef = this.dialog.open(AddMemberDialogComponent, {
      width: '500px',
      data: {group},
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        handleSuccessSnackbar(this.snackBar, 'Member added successfully');
        this.loadGroups();
      }
    });
  }

  applyGroupFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }

  applyUsageFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.usageDataSource.filter = filterValue.trim().toLowerCase();
  }
}
