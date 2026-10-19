package com.networkbasics.students;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

/** What PUT /students/{id} accepts - the client must send the full resource. */
public record StudentUpdate(
        @NotBlank String name,
        @NotBlank @Email String email,
        @NotBlank String grade) {
}
