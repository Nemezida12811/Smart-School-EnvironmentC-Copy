import jwt from 'jsonwebtoken';

class AuthService {
    static generateToken(userId) {
        if (!process.env.JWT_SECRET) {
            throw new Error("JWT_SECRET is not set");
        }

        return jwt.sign({ userId }, process.env.JWT_SECRET, { expiresIn: '7d' });
    }

    static verifyToken(token) {
        if (!process.env.JWT_SECRET) {
            throw new Error("JWT_SECRET is not set");
        }

        try {
            return jwt.verify(token, process.env.JWT_SECRET);
        } catch (error) {
            throw new Error('Invalid token');
        }
    }

    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static validatePassword(password) {
        return password && password.length >= 6;
    }
}

export default AuthService;