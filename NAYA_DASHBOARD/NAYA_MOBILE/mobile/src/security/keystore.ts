/**
 * NAYA Mobile — Secure Keystore
 * Handles device-bound key generation, storage and HMAC signature
 */

import { Capacitor } from '@capacitor/core';

const NAYA_KEY_ALIAS = 'naya_device_identity_v2';
const NAYA_SIG_KEY   = 'naya_signature_key_v2';

/**
 * Derives a stable device key using SubtleCrypto + device fingerprint.
 * Falls back to localStorage hash on unsupported platforms.
 */
export async function getDeviceKey(): Promise<string> {
  const stored = localStorage.getItem(NAYA_KEY_ALIAS);
  if (stored) return stored;

  const fingerprint = await buildFingerprint();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(fingerprint),
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: new TextEncoder().encode('naya_v6_salt'), iterations: 100000, hash: 'SHA-256' },
    keyMaterial,
    256
  );
  const deviceKey = Array.from(new Uint8Array(bits))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  localStorage.setItem(NAYA_KEY_ALIAS, deviceKey);
  return deviceKey;
}

/**
 * Signs a payload with the device key — used for command authentication.
 */
export async function signPayload(payload: string): Promise<string> {
  const deviceKey = await getDeviceKey();
  const keyData = new TextEncoder().encode(deviceKey.slice(0, 32));
  const cryptoKey = await crypto.subtle.importKey(
    'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', cryptoKey, new TextEncoder().encode(payload));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));
}

/**
 * Verifies a HMAC signature from the server.
 */
export async function verifySignature(payload: string, signature: string): Promise<boolean> {
  try {
    const expected = await signPayload(payload);
    return expected === signature;
  } catch {
    return false;
  }
}

/**
 * Clears device identity — call on logout or security reset.
 */
export function clearDeviceIdentity(): void {
  localStorage.removeItem(NAYA_KEY_ALIAS);
  localStorage.removeItem(NAYA_SIG_KEY);
}

async function buildFingerprint(): Promise<string> {
  const parts = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
    Capacitor.getPlatform(),
  ];
  return parts.join('|');
}
