package com.autodev.platform.exception;

public class DuplicateProjectKeyException extends RuntimeException {
    public DuplicateProjectKeyException(String projectKey) {
        super("A project with key '" + projectKey + "' already exists");
    }
}
