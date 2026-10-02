import BaseRoute from './base-route.js';
import User from '../db/models/User.js';
import AuthService from '../services/auth.service.js';
import { verifyTokenMiddleware } from '../middleware/auth.middleware.js';

class AuthRoutes extends BaseRoute {
    constructor() {
        super();
        this.setupRoutes();
    }

    setupRoutes() {
        // POST /api/auth/register - User registration
        this.register = async (req, res) => {
            console.log('POST /api/auth/register', { body: req.body });
            try {
                const { username, email, password } = req.body;

                if (!username || !email || !password) {
                    return this.sendError(res, 400, 'All fields are required');
                }

                if (!AuthService.validateEmail(email)) {
                    return this.sendError(res, 400, 'Invalid email format');
                }

                if (!AuthService.validatePassword(password)) {
                    return this.sendError(res, 400, 'Password must be at least 6 characters');
                }

                const existingUser = await User.findByEmail(email);
                if (existingUser) {
                    return this.sendError(res, 400, 'User with this email already exists');
                }

                const user = new User({ username, email, password });
                const result = await user.save();

                const token = AuthService.generateToken(result.insertedId.toString());

                this.sendSuccessResponse(res, {
                    message: "User registered successfully",
                    token,
                    user: {
                        id: result.insertedId.toString(),
                        username,
                        email,
                        role: 'user'
                    }
                }, 201);
            } catch (error) {
                console.error('❌ Error in register:', error);
                this.sendError(res, 500, 'Registration failed', {
                    message: error.message
                });
            }
        };

        // POST /api/auth/login - User login
        this.login = async (req, res) => {
            console.log('POST /api/auth/login', { email: req.body.email });
            try {
                const { email, password } = req.body;

                if (!email || !password) {
                    return this.sendError(res, 400, 'Email and password are required');
                }

                const user = await User.findByEmail(email);
                if (!user) {
                    return this.sendError(res, 401, 'Invalid credentials');
                }

                const isValidPassword = await User.comparePassword(password, user.password);
                if (!isValidPassword) {
                    return this.sendError(res, 401, 'Invalid credentials');
                }

                const token = AuthService.generateToken(user._id.toString());

                this.sendSuccessResponse(res, {
                    message: "Login successful",
                    token,
                    user: User.toJSON(user)
                });
            } catch (error) {
                console.error('❌ Error in login:', error);
                this.sendError(res, 500, 'Login failed', {
                    message: error.message
                });
            }
        };

        // POST /api/auth/logout - User logout
        this.logout = async (req, res) => {
            console.log('POST /api/auth/logout');
            try {
                this.sendSuccessResponse(res, {
                    message: "Logout successful"
                });
            } catch (error) {
                console.error('❌ Error in logout:', error);
                this.sendError(res, 500, 'Logout failed', {
                    message: error.message
                });
            }
        };

        // GET /api/auth/me - Get current user info (requires authentication)
        this.getMe = async (req, res) => {
            const userId = req.user.id;
            console.log('GET /api/auth/me', { userId });
            try {
                const user = await User.findById(userId);
                if (!user) {
                    return this.sendError(res, 404, 'User not found');
                }

                this.sendSuccessResponse(res, User.toJSON(user));
            } catch (error) {
                console.error('❌ Error in getMe:', error);
                this.sendError(res, 500, 'Failed to get user info', {
                    message: error.message
                });
            }
        };
    }

    registerRoutes(app) {
        app.post('/api/auth/register', this.register.bind(this));
        app.post('/api/auth/login', this.login.bind(this));
        app.post('/api/auth/logout', this.logout.bind(this));
        app.get('/api/auth/me', verifyTokenMiddleware, this.getMe.bind(this));
    }
}

export default AuthRoutes;
