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

import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {RouterModule} from '@angular/router';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatTableModule} from '@angular/material/table';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatSortModule} from '@angular/material/sort';
import {MatDialogModule} from '@angular/material/dialog';
import {MatSelectModule} from '@angular/material/select';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatTooltipModule} from '@angular/material/tooltip';
import {SharedModule} from '../common/shared.module';

import {MediaTemplatesManagementComponent} from './media-templates-management/media-templates-management.component';
import {MediaTemplateFormComponent} from './media-templates-management/media-template-form/media-template-form.component';
import {SourceAssetsManagementComponent} from './source-assets-management/source-assets-management.component';
import {SourceAssetFormComponent} from './source-assets-management/source-asset-form/source-asset-form.component';
import {SourceAssetUploadFormComponent} from './source-assets-management/source-asset-upload-form/source-asset-upload-form.component';
import {MediaGalleryManagementComponent} from './media-gallery-management/media-gallery-management.component';
import {TagsManagementComponent} from './tags-management/tags-management.component';

/**
 * This module holds deprecated admin components that are no longer accessible via routes
 * but are kept here to avoid breaking the build. These can be safely deleted in a future cleanup.
 */
@NgModule({
  declarations: [
    MediaTemplatesManagementComponent,
    MediaTemplateFormComponent,
    SourceAssetsManagementComponent,
    SourceAssetFormComponent,
    SourceAssetUploadFormComponent,
    MediaGalleryManagementComponent,
    TagsManagementComponent,
  ],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatDialogModule,
    MatSelectModule,
    MatCheckboxModule,
    MatTooltipModule,
  ],
})
export class AdminDeprecatedModule {}
