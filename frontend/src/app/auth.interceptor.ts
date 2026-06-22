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
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse,
} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {catchError, switchMap} from 'rxjs/operators';
import {AuthService} from './common/services/auth.service';
import {environment} from '../environments/environment';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  private normalizeUrl(url: string): string {
    return url.replace(/\/+$/, '');
  }

  private shouldAttachToken(request: HttpRequest<unknown>): boolean {
    // Skip local static assets and non-backend requests.
    if (
      request.url.startsWith('assets/') ||
      request.url.startsWith('/assets/') ||
      request.url.startsWith('./assets/')
    ) {
      return false;
    }

    const backendBaseUrl = this.normalizeUrl(environment.backendURL || '');
    if (!backendBaseUrl) {
      return false;
    }

    const requestUrl = this.normalizeUrl(request.url);
    return requestUrl.startsWith(backendBaseUrl);
  }

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    if (!this.shouldAttachToken(request)) {
      return next.handle(request);
    }

    // Asynchronously get a valid token. This will use the cache or trigger a silent refresh.
    return this.authService.getValidIdentityPlatformToken$().pipe(
      switchMap(token => {
        // Token was retrieved successfully. Clone the request and add the auth header.
        const authorizedRequest = request.clone({
          setHeaders: {Authorization: `Bearer ${token}`},
        });
        return next.handle(authorizedRequest);
      }),
      catchError(error => {
        // If the error is NOT an HttpErrorResponse, it's a token refresh failure
        // from our AuthService. In this case, the session is invalid, and we should log out.
        if (!(error instanceof HttpErrorResponse)) {
          console.error(
            'AuthInterceptor: Session expired and could not be refreshed. Logging out.',
            error,
          );
          // Only force-logout if the user had an active session. Avoids calling
          // logout() for pre-login requests which would race against the sign-in
          // flow and clear the freshly-obtained token before the backend
          // handshake completes, causing "User session is not valid or has expired".
          if (this.authService.isUserLoggedIn()) {
            void this.authService.logout();
          }
        }

        // Otherwise, it's a backend API error (e.g., 404, 500). We should NOT log out.
        // We just re-throw the original HttpErrorResponse so the calling service
        // (e.g., UserService) can handle it and display an appropriate error message.
        return throwError(() => error);
      }),
    );
  }
}
