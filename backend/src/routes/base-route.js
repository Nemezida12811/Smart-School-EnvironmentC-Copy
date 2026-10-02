class BaseRoute {
    /**
     * @param {Response} res - Express response object
     * @param {Object} data - Data to send
     * @param {number} statusCode - HTTP status code (default 200)
     */
    sendSuccessResponse(res, data = {}, statusCode = 200) {
        res.status(statusCode).json({
            success: true,
            data
        });
    }

    /**
     * @param {Response} res - Express response object
     * @param {number} statusCode - HTTP status code
     * @param {string} message - Error message
     * @param {Object} details - Additional error details
     */
    sendError(res, statusCode, message, details = null) {
        const response = {
            success: false,
            error: {
                message,
                statusCode
            }
        };

        if (details) {
            response.error.details = details;
        }

        res.status(statusCode).json(response);
    }
}

export default BaseRoute;
