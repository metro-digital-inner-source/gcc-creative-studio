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
import {HttpClient, HttpHeaders, HttpParams} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {catchError} from 'rxjs/operators';
import {environment} from '../../../environments/environment';

export interface AllowlistEntry {
  id: number;
  email: string | null;
  domain: string | null;
  isActive: boolean;
  notes: string;
  createdBy: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface AllowlistCreateDto {
  email?: string;
  domain?: string;
  notes?: string;
}

export interface AllowlistUpdateDto {
  isActive?: boolean;
  notes?: string;
}

@Injectable({
  providedIn: 'root',
})
export class AllowlistService {
  private readonly apiUrl = `${environment.backendURL}/admin/allowlist`;

  private readonly httpOptions = {
    headers: new HttpHeaders({'Content-Type': 'application/json'}),
  };

  constructor(private http: HttpClient) {}

  list(activeOnly = false): Observable<AllowlistEntry[]> {
    const params = new HttpParams().set('active_only', activeOnly ? 'true' : 'false');
    return this.http
      .get<AllowlistEntry[]>(this.apiUrl, {...this.httpOptions, params})
      .pipe(catchError(this.handleError));
  }

  create(dto: AllowlistCreateDto): Observable<AllowlistEntry> {
    return this.http
      .post<AllowlistEntry>(this.apiUrl, dto, this.httpOptions)
      .pipe(catchError(this.handleError));
  }

  update(id: number, dto: AllowlistUpdateDto): Observable<AllowlistEntry> {
    return this.http
      .put<AllowlistEntry>(`${this.apiUrl}/${id}`, dto, this.httpOptions)
      .pipe(catchError(this.handleError));
  }

  delete(id: number): Observable<void> {
    return this.http
      .delete<void>(`${this.apiUrl}/${id}`, this.httpOptions)
      .pipe(catchError(this.handleError));
  }

  clearCache(): Observable<{message: string}> {
    return this.http
      .post<{message: string}>(`${this.apiUrl}/cache/clear`, {}, this.httpOptions)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: any): Observable<never> {
    const message =
      error?.error?.detail || error?.message || 'An unexpected error occurred.';
    return throwError(() => new Error(message));
  }
}
