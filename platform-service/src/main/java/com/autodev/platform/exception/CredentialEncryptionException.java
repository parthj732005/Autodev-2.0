package com.autodev.platform.exception;

/** Thrown when a provider credential cannot be safely encrypted or decrypted
 * (missing/malformed master key, or corrupted stored ciphertext). Never
 * caught to fall back to plaintext — callers must fail the request. */
public class CredentialEncryptionException extends RuntimeException {
    public CredentialEncryptionException(String message) {
        super(message);
    }

    public CredentialEncryptionException(String message, Throwable cause) {
        super(message, cause);
    }
}
