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
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {AdminRoutingModule} from './admin-routing.module';
import {AdminLayoutComponent} from './admin-layout/admin-layout.component';
import {UsersManagementComponent} from './users-management/users-management.component';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatListModule} from '@angular/material/list';
import {MatIconModule} from '@angular/material/icon';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatButtonModule} from '@angular/material/button';
import {MatTableModule} from '@angular/material/table';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatSortModule} from '@angular/material/sort';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatTooltipModule} from '@angular/material/tooltip';
import {UserFormComponent} from './users-management/user-form.component';
import {MatDialogModule} from '@angular/material/dialog';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatChipsModule} from '@angular/material/chips';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatTabsModule} from '@angular/material/tabs';
import {MatSelectModule} from '@angular/material/select';
import {MatMenuModule} from '@angular/material/menu';
import {MatDividerModule} from '@angular/material/divider';
import {MatStepperModule} from '@angular/material/stepper';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatCardModule} from '@angular/material/card';
import {ScrollingModule} from '@angular/cdk/scrolling';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {MatNativeDateModule} from '@angular/material/core';
import {SharedModule} from '../common/shared.module';
import {AdminHomeComponent} from './admin-home/admin-home.component';
import {GroupsManagementComponent} from './groups-management/groups-management.component';
import {CreateGroupDialogComponent} from './groups-management/create-group-dialog/create-group-dialog.component';
import {AddMemberDialogComponent} from './groups-management/add-member-dialog/add-member-dialog.component';
import {AdminDeprecatedModule} from './admin-deprecated.module';

@NgModule({
  declarations: [
    AdminLayoutComponent,
    UsersManagementComponent,
    UserFormComponent,
    AdminHomeComponent,
    GroupsManagementComponent,
    CreateGroupDialogComponent,
    AddMemberDialogComponent,
  ],
  imports: [
    CommonModule,
    SharedModule,
    AdminRoutingModule,
    AdminDeprecatedModule,
    MatSidenavModule,
    MatListModule,
    MatPaginatorModule,
    MatSortModule,
    MatDialogModule,
    MatSnackBarModule,
    MatTooltipModule,
    MatToolbarModule,
    MatDividerModule,
    MatButtonModule,
    MatChipsModule,
    MatIconModule,
    MatStepperModule,
    MatFormFieldModule,
    MatInputModule,
    ReactiveFormsModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatMenuModule,
    MatCheckboxModule,
    MatCardModule,
    MatTableModule,
    FormsModule,
    ScrollingModule,
    MatProgressBarModule,
    MatExpansionModule,
    MatTabsModule,
    MatDatepickerModule,
    MatNativeDateModule,
  ],
})
export class AdminModule {}
