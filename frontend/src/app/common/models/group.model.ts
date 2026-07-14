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

export enum GroupMemberRole {
  MEMBER = 'member',
  ADMIN = 'admin',
}

export interface GroupMember {
  userId: number;
  email: string;
  name: string;
  role: GroupMemberRole;
  joinedAt: string;
}

export interface Group {
  id: number;
  name: string;
  countryCode?: string;
  sharedWorkspaceId: number;
  members: GroupMember[];
  memberCount?: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateGroupRequest {
  name: string;
  countryCode?: string;
}

export interface AddMemberRequest {
  userId: number;
  role: GroupMemberRole;
}

export interface ShareItemsRequest {
  groupId: number;
  mediaItemIds: number[];
}

export interface GroupUsageSummary {
  totalGroups: number;
  totalMembers: number;
  totalSpendUsd: number;
  totalTokensConsumed: number;
}

export interface GroupUsageBreakdown {
  groupId: number;
  groupName: string;
  countryCode?: string;
  memberCount: number;
  spendUsd: number;
  tokensConsumed: number;
  activityCount: number;
}

export interface MyUsageResponse {
  groupId: number;
  groupName: string;
  userSpendUsd: number;
  userTokensConsumed: number;
  userActivityCount: number;
  groupTotalSpendUsd: number;
  groupTotalTokens: number;
}
