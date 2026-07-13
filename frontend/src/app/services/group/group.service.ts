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

import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';
import {
  Group,
  CreateGroupRequest,
  ShareItemsRequest,
  MyUsageResponse,
  GroupUsageSummary,
  GroupUsageBreakdown,
  AddMemberRequest,
} from '../../common/models/group.model';

@Injectable({
  providedIn: 'root',
})
export class GroupService {
  private apiUrl = `${environment.backendURL}/groups`;
  private adminApiUrl = `${environment.backendURL}/admin/groups`;

  constructor(private http: HttpClient) {}

  // User endpoints

  /**
   * Get all groups the current user is a member of
   */
  getMyGroups(): Observable<Group[]> {
    return this.http.get<Group[]>(`${this.apiUrl}/me`);
  }

  /**
   * Create a new group
   */
  createGroup(request: CreateGroupRequest): Observable<Group> {
    return this.http.post<Group>(this.apiUrl, request);
  }

  /**
   * Share media items to a group
   */
  shareItemsToGroup(request: ShareItemsRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/share-items`, request);
  }

  /**
   * Get usage statistics for the current user
   */
  getMyUsage(startDate?: string, endDate?: string): Observable<MyUsageResponse> {
    let params = new HttpParams();
    if (startDate) {
      params = params.set('start_date', startDate);
    }
    if (endDate) {
      params = params.set('end_date', endDate);
    }
    return this.http.get<MyUsageResponse>(`${this.apiUrl}/my-usage`, {params});
  }

  // Admin endpoints

  /**
   * Get all groups (admin only)
   */
  getAllGroups(): Observable<Group[]> {
    return this.http.get<Group[]>(this.adminApiUrl);
  }

  /**
   * Create a group as admin
   */
  createGroupAdmin(name: string, countryCode?: string): Observable<Group> {
    const params = new HttpParams()
      .set('name', name)
      .set('country_code', countryCode || '');
    return this.http.post<Group>(this.adminApiUrl, null, {params});
  }

  /**
   * Add a user to a group (admin only)
   */
  addUserToGroup(
    groupId: number,
    userId: number,
    role: string = 'member',
  ): Observable<Group> {
    const params = new HttpParams()
      .set('user_id', userId.toString())
      .set('role', role);
    return this.http.post<Group>(
      `${this.adminApiUrl}/${groupId}/users`,
      null,
      {params},
    );
  }

  /**
   * Get aggregate usage summary (admin only)
   */
  getUsageSummary(
    startDate?: string,
    endDate?: string,
  ): Observable<GroupUsageSummary> {
    let params = new HttpParams();
    if (startDate) {
      params = params.set('start_date', startDate);
    }
    if (endDate) {
      params = params.set('end_date', endDate);
    }
    return this.http.get<GroupUsageSummary>(
      `${this.adminApiUrl}/usage-summary`,
      {params},
    );
  }

  /**
   * Get per-group usage breakdown (admin only)
   */
  getUsageBreakdown(
    startDate?: string,
    endDate?: string,
  ): Observable<GroupUsageBreakdown[]> {
    let params = new HttpParams();
    if (startDate) {
      params = params.set('start_date', startDate);
    }
    if (endDate) {
      params = params.set('end_date', endDate);
    }
    return this.http.get<GroupUsageBreakdown[]>(
      `${this.adminApiUrl}/usage-breakdown`,
      {params},
    );
  }
}
