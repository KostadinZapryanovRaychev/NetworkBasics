package com.networkbasics.students;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

/** What POST /students accepts - the equivalent of schemas.StudentCreate. */
public record StudentCreate(
        @NotBlank String name,
        @NotBlank @Email String email,
        @NotBlank String grade) {
}
