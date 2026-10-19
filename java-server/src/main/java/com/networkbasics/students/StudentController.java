package com.networkbasics.students;

import java.util.List;
import java.util.Map;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

/**
 * Same routes, same methods, same status codes as the Python version's
 * main.py - just written against Spring MVC instead of FastAPI.
 */
@RestController
public class StudentController {

    private final StudentRepository repository;

    public StudentController(StudentRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @GetMapping("/students")
    public List<StudentOut> listStudents() {
        return repository.findAll().stream().map(StudentOut::from).toList();
    }

    @GetMapping("/students/{id}")
    public StudentOut getStudent(@PathVariable Long id) {
        return StudentOut.from(findOrThrow(id));
    }

    @PostMapping("/students")
    @ResponseStatus(HttpStatus.CREATED)
    public StudentOut createStudent(@Valid @RequestBody StudentCreate payload) {
        Student student = new Student(payload.name(), payload.email(), payload.grade());
        return StudentOut.from(repository.save(student));
    }

    @PutMapping("/students/{id}")
    public StudentOut replaceStudent(@PathVariable Long id, @Valid @RequestBody StudentUpdate payload) {
        Student student = findOrThrow(id);
        student.setName(payload.name());
        student.setEmail(payload.email());
        student.setGrade(payload.grade());
        return StudentOut.from(repository.save(student));
    }

    @PatchMapping("/students/{id}")
    public StudentOut updateStudent(@PathVariable Long id, @Valid @RequestBody StudentPatch payload) {
        Student student = findOrThrow(id);
        if (payload.name() != null) {
            student.setName(payload.name());
        }
        if (payload.email() != null) {
            student.setEmail(payload.email());
        }
        if (payload.grade() != null) {
            student.setGrade(payload.grade());
        }
        return StudentOut.from(repository.save(student));
    }

    @DeleteMapping("/students/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteStudent(@PathVariable Long id) {
        Student student = findOrThrow(id);
        repository.delete(student);
    }

    @GetMapping("/grades")
    public List<String> listGrades() {
        return repository.findDistinctGrades();
    }

    private Student findOrThrow(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Student not found"));
    }
}
