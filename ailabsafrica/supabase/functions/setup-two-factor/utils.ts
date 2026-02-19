/**
 * Generate backup codes for 2FA
 * @returns Array of 8 backup codes, each 8 characters long
 */
export function generateBackupCodes(): string[] {
	const codes: string[] = []
	const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

	for (let i = 0; i < 8; i++) {
		let code = ''
		for (let j = 0; j < 8; j++) {
			code += chars.charAt(Math.floor(Math.random() * chars.length))
		}
		codes.push(code)
	}

	return codes
}

/**
 * Verify a TOTP code against a secret
 * @param secret - The TOTP secret
 * @param code - The 6-digit code to verify
 * @returns boolean indicating if the code is valid
 */
export function verifyTOTPCode(secret: string, code: string): boolean {
	try {
		const { generateTOTP } = require('https://esm.sh/otplib@12.0.1')
		const currentCode = generateTOTP(secret)
		return currentCode === code
	} catch (error) {
		console.error('Error verifying TOTP code:', error)
		return false
	}
}

/**
 * Verify a backup code
 * @param storedCodes - Array of stored backup codes
 * @param providedCode - The backup code provided by user
 * @returns boolean indicating if the backup code is valid
 */
export function verifyBackupCode(storedCodes: string[], providedCode: string): boolean {
	return storedCodes.includes(providedCode.toUpperCase())
}
