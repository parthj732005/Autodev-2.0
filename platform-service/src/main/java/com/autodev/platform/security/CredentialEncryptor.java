package com.autodev.platform.security;

import com.autodev.platform.exception.CredentialEncryptionException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;

/**
 * AES-256-GCM encryption for provider API keys at rest. The master key comes
 * from {@code AUTODEV_CREDENTIAL_ENCRYPTION_KEY} (via
 * {@code platform.credential-encryption-key}) — a Base64-encoded 32-byte
 * (256-bit) key. Never falls back to plaintext: a missing, malformed, or
 * wrong-size key throws {@link CredentialEncryptionException} at the point of
 * use rather than at application startup, so the app can still boot without
 * this configured until a user actually tries to save a provider credential.
 *
 * Stored format: base64(iv[12 bytes] || ciphertext+tag). A fresh random IV is
 * generated per encryption (GCM requires a unique IV per key+message).
 */
@Component
public class CredentialEncryptor {

    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private static final int IV_LENGTH_BYTES = 12;
    private static final int TAG_LENGTH_BITS = 128;
    private static final int REQUIRED_KEY_BYTES = 32;

    private final String rawKeyBase64;

    public CredentialEncryptor(@Value("${platform.credential-encryption-key:}") String rawKeyBase64) {
        this.rawKeyBase64 = rawKeyBase64;
    }

    public String encrypt(String plaintext) {
        if (plaintext == null) {
            return null;
        }
        SecretKey key = resolveKey();
        try {
            byte[] iv = new byte[IV_LENGTH_BYTES];
            new SecureRandom().nextBytes(iv);

            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(TAG_LENGTH_BITS, iv));
            byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));

            ByteBuffer buffer = ByteBuffer.allocate(iv.length + ciphertext.length);
            buffer.put(iv).put(ciphertext);
            return Base64.getEncoder().encodeToString(buffer.array());
        } catch (Exception e) {
            throw new CredentialEncryptionException("Failed to encrypt credential", e);
        }
    }

    public String decrypt(String stored) {
        if (stored == null) {
            return null;
        }
        SecretKey key = resolveKey();
        try {
            byte[] all = Base64.getDecoder().decode(stored);
            if (all.length <= IV_LENGTH_BYTES) {
                throw new CredentialEncryptionException("Stored credential data is invalid (too short)");
            }
            byte[] iv = Arrays.copyOfRange(all, 0, IV_LENGTH_BYTES);
            byte[] ciphertext = Arrays.copyOfRange(all, IV_LENGTH_BYTES, all.length);

            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(TAG_LENGTH_BITS, iv));
            byte[] plaintext = cipher.doFinal(ciphertext);
            return new String(plaintext, StandardCharsets.UTF_8);
        } catch (CredentialEncryptionException e) {
            throw e;
        } catch (IllegalArgumentException e) {
            throw new CredentialEncryptionException("Stored credential data is not valid Base64", e);
        } catch (Exception e) {
            // Covers AEADBadTagException (corrupted data or wrong key) and any
            // other cipher failure — never distinguish further to the caller.
            throw new CredentialEncryptionException(
                    "Failed to decrypt credential — data may be corrupted or the encryption key changed", e);
        }
    }

    private SecretKey resolveKey() {
        if (rawKeyBase64 == null || rawKeyBase64.isBlank()) {
            throw new CredentialEncryptionException(
                    "AUTODEV_CREDENTIAL_ENCRYPTION_KEY is not configured — cannot encrypt/decrypt provider credentials");
        }
        byte[] keyBytes;
        try {
            keyBytes = Base64.getDecoder().decode(rawKeyBase64);
        } catch (IllegalArgumentException e) {
            throw new CredentialEncryptionException(
                    "AUTODEV_CREDENTIAL_ENCRYPTION_KEY is not valid Base64");
        }
        if (keyBytes.length != REQUIRED_KEY_BYTES) {
            throw new CredentialEncryptionException(
                    "AUTODEV_CREDENTIAL_ENCRYPTION_KEY must decode to exactly 32 bytes (256-bit AES key); got "
                            + keyBytes.length + " bytes");
        }
        return new SecretKeySpec(keyBytes, "AES");
    }
}
