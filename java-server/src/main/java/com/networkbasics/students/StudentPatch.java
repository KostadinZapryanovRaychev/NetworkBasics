package com.networkbasics.students;

import jakarta.validation.constraints.Email;

/** What PATCH /students/{id} accepts - every field optional, only sent fields change. */
public record StudentPatch(
        String name,
        @Email String email,
        String grade) {
}
