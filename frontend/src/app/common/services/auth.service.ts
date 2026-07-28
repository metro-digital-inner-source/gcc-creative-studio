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

import {Injectable, PLATFORM_ID, inject} from '@angular/core';
import {Router} from '@angular/router';
import {UserModel, UserRolesEnum} from '../models/user.model';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {environment} from '../../../environments/environment';
import {UserService} from '../services/user.service';
import {Observable, throwError} from 'rxjs';
import {catchError, tap} from 'rxjs/operators';
import {isPlatformBrowser} from '@angular/common';

const USER_DETAILS = 'USER_DETAILS';
const LOCAL_SESSION_KEY = 'local_auth_session';
const LOGIN_ROUTE = '/login';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private platformId = inject(PLATFORM_ID);
  private localUserEmail: string | null = null;

  constructor(
    private router: Router,
    private httpClient: HttpClient,
    private userService: UserService,
  ) {
    this.loadLocalSession();
  }

  /**
   * Deployed (IAP): sync profile from backend using IAP identity forwarded by nginx.
   * Local: establish a dev session for environment.localUserEmail.
   */
  establishSession$(): Observable<UserModel> {
    if (environment.isLocal) {
      this.localUserEmail = environment.localUserEmail;
      if (isPlatformBrowser(this.platformId)) {
        localStorage.setItem(LOCAL_SESSION_KEY, this.localUserEmail);
      }
    }
    return this.syncUserWithBackend$();
  }

  private syncUserWithBackend$(): Observable<UserModel> {
    return this.httpClient
      .get<UserModel>(`${environment.backendURL}/users/me`)
      .pipe(
        tap((userDetails: UserModel) => {
          if (isPlatformBrowser(this.platformId)) {
            localStorage.setItem(USER_DETAILS, JSON.stringify(userDetails));
          }
        }),
        catchError((error: HttpErrorResponse) => {
          console.error('Failed to sync user with backend', error);
          return throwError(
            () =>
              new Error(
                error?.error?.detail ||
                  'Could not synchronize user profile with the server.',
              ),
          );
        }),
      );
  }

  async logout(route: string = LOGIN_ROUTE) {
    this.clearLocalSession();

    if (!environment.isLocal && environment.iapClientId) {
      const continueUrl = encodeURIComponent(window.location.origin);
      window.location.href =
        `https://iap.googleapis.com/v1/oauth/clientIds/` +
        `${environment.iapClientId}:logout?continue=${continueUrl}`;
      return;
    }

    void this.router.navigateByUrl(route);
  }

  /** Clear browser session state without hitting IAP logout. */
  clearLocalSession(): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem(USER_DETAILS);
      localStorage.removeItem(LOCAL_SESSION_KEY);
      localStorage.removeItem('showTooltip');
    }
    this.localUserEmail = null;
  }

  isLoggedIn(): boolean {
    if (!isPlatformBrowser(this.platformId)) return false;

    const user = this.userService.getUserDetails();
    const hasProfile = !!(user?.email);
    if (!hasProfile && this.router.url !== LOGIN_ROUTE) {
      void this.router.navigate([LOGIN_ROUTE]);
    }
    return hasProfile;
  }

  isUserLoggedIn(): boolean {
    if (!isPlatformBrowser(this.platformId)) return false;
    return !!(this.userService.getUserDetails()?.email);
  }

  isUserAdmin(): boolean {
    if (!isPlatformBrowser(this.platformId)) return false;
    const user_role = this.userService.getUserDetails()?.roles;
    return user_role?.includes(UserRolesEnum.ADMIN) || false;
  }

  isUserWorkflows(): boolean {
    if (!isPlatformBrowser(this.platformId)) return false;
    const user_role = this.userService.getUserDetails()?.roles;
    return user_role?.includes(UserRolesEnum.WORKFLOWS) || false;
  }

  /** Local-only identity header value for the auth interceptor. */
  getLocalUserEmailHeader(): string | null {
    if (!environment.isLocal || !this.localUserEmail) return null;
    return `accounts.google.com:${this.localUserEmail}`;
  }

  private loadLocalSession(): void {
    if (!isPlatformBrowser(this.platformId) || !environment.isLocal) return;
    this.localUserEmail = localStorage.getItem(LOCAL_SESSION_KEY);
  }
}
