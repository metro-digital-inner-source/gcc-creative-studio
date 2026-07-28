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
import {catchError} from 'rxjs/operators';
import {AuthService} from './common/services/auth.service';
import {environment} from '../environments/environment';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    let outbound = request;

    // Deployed: IAP JWT is attached by Google in front of Cloud Run and
    // forwarded by nginx. Local: send a synthetic IAP email header.
    if (environment.isLocal) {
      const emailHeader = this.authService.getLocalUserEmailHeader();
      if (emailHeader) {
        outbound = request.clone({
          setHeaders: {'X-Goog-Authenticated-User-Email': emailHeader},
        });
      }
    }

    return next.handle(outbound).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          console.error('AuthInterceptor: unauthorized. Logging out.', error);
          void this.authService.logout();
        }
        return throwError(() => error);
      }),
    );
  }
}
