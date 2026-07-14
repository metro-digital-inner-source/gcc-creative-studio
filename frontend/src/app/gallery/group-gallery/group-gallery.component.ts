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

import {Component, OnInit, Inject, PLATFORM_ID} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {MatDialog} from '@angular/material/dialog';
import {MatSnackBar} from '@angular/material/snack-bar';
import {GroupService} from '../../services/group/group.service';
import {Group} from '../../common/models/group.model';
import {GalleryService} from '../gallery.service';
import {WorkspaceStateService} from '../../services/workspace/workspace-state.service';
import {GalleryItem} from '../../common/models/gallery-item.model';
import {Subscription} from 'rxjs';

@Component({
  selector: 'app-group-gallery',
  templateUrl: './group-gallery.component.html',
  styleUrls: ['./group-gallery.component.scss'],
  providers: [GalleryService],
})
export class GroupGalleryComponent implements OnInit {
  groups: Group[] = [];
  selectedGroup: Group | null = null;
  isLoadingGroups = true;
  images: GalleryItem[] = [];
  selectedItems: Set<string> = new Set();
  isLoading = true;
  isRestoring = false;
  allImagesLoaded = false;

  private imagesSubscription: Subscription | undefined;
  private loadingSubscription: Subscription | undefined;
  private allImagesLoadedSubscription: Subscription | undefined;
  isBrowser: boolean;

  constructor(
    private groupService: GroupService,
    private galleryService: GalleryService,
    private workspaceStateService: WorkspaceStateService,
    private snackBar: MatSnackBar,
    public dialog: MatDialog,
    @Inject(PLATFORM_ID) platformId: Object,
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngOnInit(): void {
    this.loadGroups();
    this.setupGallerySubscriptions();
  }

  ngOnDestroy(): void {
    this.imagesSubscription?.unsubscribe();
    this.loadingSubscription?.unsubscribe();
    this.allImagesLoadedSubscription?.unsubscribe();
  }

  private setupGallerySubscriptions(): void {
    this.loadingSubscription = this.galleryService.isLoading$.subscribe(
      loading => {
        this.isLoading = loading;
      },
    );

    this.imagesSubscription = this.galleryService.images$.subscribe(images => {
      if (images) {
        this.images = images as GalleryItem[];
      }
    });

    this.allImagesLoadedSubscription =
      this.galleryService.allImagesLoaded.subscribe(loaded => {
        this.allImagesLoaded = loaded;
      });
  }

  loadGroups(): void {
    this.groupService.getMyGroups().subscribe({
      next: groups => {
        this.groups = groups;
        this.isLoadingGroups = false;
        // Auto-select first group if available
        if (groups.length > 0 && !this.selectedGroup) {
          this.selectGroup(groups[0]);
        }
      },
      error: error => {
        console.error('Failed to load groups:', error);
        this.snackBar.open('Failed to load groups', 'Close', {
          duration: 3000,
        });
        this.isLoadingGroups = false;
      },
    });
  }

  selectGroup(group: Group): void {
    this.selectedGroup = group;
    this.selectedItems.clear();
    // Load gallery items for this group's workspace
    if (this.isBrowser) {
      this.workspaceStateService.setActiveWorkspaceId(group.sharedWorkspaceId);
      this.galleryService.setFilters({
        limit: 20,
        offset: 0,
        workspaceId: group.sharedWorkspaceId,
      });
      this.galleryService.loadGallery(true);
    }
  }

  toggleSelection(item: GalleryItem, event?: MouseEvent): void {
    const id = `${item.itemType}:${item.id}`;
    if (this.selectedItems.has(id)) {
      this.selectedItems.delete(id);
    } else {
      this.selectedItems.add(id);
    }
  }

  isItemSelected(item: GalleryItem): boolean {
    return this.selectedItems.has(`${item.itemType}:${item.id}`);
  }

  selectAll(): void {
    if (this.isAllSelected) {
      this.selectedItems.clear();
    } else {
      this.images.forEach(img => {
        this.selectedItems.add(`${img.itemType}:${img.id}`);
      });
    }
  }

  get isAllSelected(): boolean {
    return (
      this.images.length > 0 && this.selectedItems.size === this.images.length
    );
  }

  get selectedMediaItemIds(): number[] {
    return Array.from(this.selectedItems)
      .filter(selection => selection.startsWith('media_item:'))
      .map(selection => parseInt(selection.split(':')[1], 10));
  }

  restoreSelected(): void {
    const mediaItemIds = this.selectedMediaItemIds;
    if (!mediaItemIds.length || this.isRestoring) return;

    if (
      !confirm(
        `Restore ${mediaItemIds.length} item(s) to their original workspace?`,
      )
    ) {
      return;
    }

    this.isRestoring = true;
    this.groupService.restoreItemsFromGroup(mediaItemIds).subscribe({
      next: response => {
        this.snackBar.open(
          `${response.item_count} item(s) restored successfully`,
          'Close',
          {duration: 3000},
        );
        this.selectedItems.clear();
        this.isRestoring = false;
        // Refresh gallery
        if (this.selectedGroup) {
          this.selectGroup(this.selectedGroup);
        }
      },
      error: err => {
        console.error('Error restoring items:', err);
        this.snackBar.open('Failed to restore items', 'Close', {
          duration: 3000,
        });
        this.isRestoring = false;
      },
    });
  }

  loadMore(): void {
    if (!this.allImagesLoaded && !this.isLoading) {
      this.galleryService.loadGallery();
    }
  }
}
