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
import {RouterModule, Routes} from '@angular/router';
import {AdminLayoutComponent} from './admin-layout/admin-layout.component';
import {UsersManagementComponent} from './users-management/users-management.component';
import {AdminHomeComponent} from './admin-home/admin-home.component';
import {GroupsManagementComponent} from './groups-management/groups-management.component';

const routes: Routes = [
  {
    path: '', // This will be '/admin' because of the main app routing
    component: AdminLayoutComponent,
    children: [
      {path: '', redirectTo: 'dashboard', pathMatch: 'full'}, // Default child route
      {path: 'dashboard', component: AdminHomeComponent},
      {path: 'users', component: UsersManagementComponent},
      {path: 'groups', component: GroupsManagementComponent},
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AdminRoutingModule {}
