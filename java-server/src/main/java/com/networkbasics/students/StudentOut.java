package com.networkbasics.students;

/** What every endpoint returns - the equivalent of schemas.StudentOut. */
public record StudentOut(Long id, String name, String email, String grade) {

    static StudentOut from(Student student) {
        return new StudentOut(student.getId(), student.getName(), student.getEmail(), student.getGrade());
    }
}
