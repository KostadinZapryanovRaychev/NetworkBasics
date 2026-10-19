package com.networkbasics.students;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

/**
 * The database access layer - the equivalent of calling db.query(...) directly
 * in the Python version's main.py. Spring Data JPA generates the implementation
 * of this interface at startup; we only declare what we need.
 */
public interface StudentRepository extends JpaRepository<Student, Long> {

    @Query("select distinct s.grade from Student s")
    List<String> findDistinctGrades();
}
