package com.networkbasics.students;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point - the equivalent of running `uvicorn app.main:app` for the Python version. */
@SpringBootApplication
public class StudentsApiApplication {
    public static void main(String[] args) {
        SpringApplication.run(StudentsApiApplication.class, args);
    }
}
