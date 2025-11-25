import { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";
import { shareConversation, getSharedUsers, removeSharedUser } from "../utils/api";

export default function ShareModal({ isOpen, onClose, conversationId, conversationName }) {
  const [emails, setEmails] = useState([""]);
  const [isSharing, setIsSharing] = useState(false);
  const [shareResult, setShareResult] = useState(null);
  const [sharedUsers, setSharedUsers] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isRemovingUser, setIsRemovingUser] = useState(null);

  const addEmailField = () => {
    setEmails([...emails, ""]);
  };

  const removeEmailField = (index) => {
    if (emails.length > 1) {
      setEmails(emails.filter((_, i) => i !== index));
    }
  };

  const updateEmail = (index, value) => {
    const newEmails = [...emails];
    newEmails[index] = value;
    setEmails(newEmails);
  };

  // Load shared users when modal opens
  const loadSharedUsers = useCallback(async () => {
    if (!conversationId) return;
    
    setIsLoadingUsers(true);
    try {
      const response = await getSharedUsers(conversationId);
      setSharedUsers(response.shared_users || []);
    } catch (error) {
      console.error('Error loading shared users:', error);
    } finally {
      setIsLoadingUsers(false);
    }
  }, [conversationId]);

  useEffect(() => {
    if (isOpen && conversationId) {
      loadSharedUsers();
    }
  }, [isOpen, conversationId, loadSharedUsers]);

  const handleRemoveUser = async (userUid) => {
    setIsRemovingUser(userUid);
    try {
      await removeSharedUser(conversationId, userUid);
      // Remove user from local state
      setSharedUsers(sharedUsers.filter(user => user.uid !== userUid));
      setShareResult({
        success: true,
        message: "User removed successfully"
      });
      // Clear result after 2 seconds
      setTimeout(() => setShareResult(null), 2000);
    } catch (error) {
      setShareResult({
        success: false,
        message: error.message || "Failed to remove user"
      });
    } finally {
      setIsRemovingUser(null);
    }
  };

  const handleShare = async () => {
    // Filter out empty emails and validate
    const validEmails = emails
      .map(email => email.trim())
      .filter(email => email.length > 0);

    if (validEmails.length === 0) {
      setShareResult({
        success: false,
        message: "Please enter at least one email address"
      });
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const invalidEmails = validEmails.filter(email => !emailRegex.test(email));
    
    if (invalidEmails.length > 0) {
      setShareResult({
        success: false,
        message: `Invalid email addresses: ${invalidEmails.join(', ')}`
      });
      return;
    }

    setIsSharing(true);
    setShareResult(null);

    try {
      const result = await shareConversation(conversationId, validEmails);
      setShareResult(result);
      
      if (result.success) {
        // Refresh the shared users list
        loadSharedUsers();
        // Clear the form after successful sharing
        setTimeout(() => {
          setEmails([""]);
          setShareResult(null);
        }, 2000);
      }
    } catch (error) {
      setShareResult({
        success: false,
        message: error.message || "Failed to share conversation"
      });
    } finally {
      setIsSharing(false);
    }
  };

  const resetModal = () => {
    setEmails([""]);
    setShareResult(null);
    setIsSharing(false);
    setSharedUsers([]);
    setIsLoadingUsers(false);
    setIsRemovingUser(null);
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Share Conversation</h2>
          <button
            onClick={handleClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            Sharing: <span className="font-semibold">{conversationName}</span>
          </p>
          <p className="text-xs text-gray-500">
            Enter email addresses of people you want to share this conversation with.
            They must have an account on this app.
          </p>
        </div>

        {/* Current Shared Users */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Currently shared with:</h3>
          {isLoadingUsers ? (
            <div className="flex items-center justify-center py-4">
              <svg className="animate-spin h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="ml-2 text-sm text-gray-500">Loading shared users...</span>
            </div>
          ) : sharedUsers.length === 0 ? (
            <p className="text-sm text-gray-500 py-2">No users currently have access</p>
          ) : (
            <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded-md p-2">
              {sharedUsers.map((user) => (
                <div key={user.uid} className="flex items-center justify-between bg-gray-50 rounded px-3 py-2">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{user.email}</p>
                    {user.display_name && (
                      <p className="text-xs text-gray-500">{user.display_name}</p>
                    )}
                  </div>
                  <button
                    onClick={() => handleRemoveUser(user.uid)}
                    disabled={isRemovingUser === user.uid || isSharing}
                    className="text-red-500 hover:text-red-700 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Remove user"
                  >
                    {isRemovingUser === user.uid ? (
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add New Users Section */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Add new users:</h3>
          <div className="space-y-3 mb-4">
            {emails.map((email, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="email"
                  placeholder="Enter email address"
                  value={email}
                  onChange={(e) => updateEmail(index, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900"
                  disabled={isSharing}
                />
                {emails.length > 1 && (
                  <button
                    onClick={() => removeEmailField(index)}
                    className="text-red-500 hover:text-red-700 font-bold text-lg"
                    disabled={isSharing}
                  >
                    −
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={addEmailField}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium mb-4 flex items-center"
            disabled={isSharing}
          >
            + Add another email
          </button>
        </div>

        {shareResult && (
          <div className={`p-3 rounded-md mb-4 text-sm ${
            shareResult.success 
              ? "bg-green-100 text-green-800 border border-green-200" 
              : "bg-red-100 text-red-800 border border-red-200"
          }`}>
            <p className="font-medium">{shareResult.message}</p>
            {shareResult.failed_emails && shareResult.failed_emails.length > 0 && (
              <p className="mt-1 text-xs">
                Failed emails: {shareResult.failed_emails.join(', ')}
              </p>
            )}
            {shareResult.shared_with && shareResult.shared_with.length > 0 && (
              <p className="mt-1 text-xs">
                Successfully shared with {shareResult.shared_with.length} users
              </p>
            )}
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition"
            disabled={isSharing}
          >
            Cancel
          </button>
          <button
            onClick={handleShare}
            disabled={isSharing}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isSharing ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Sharing...
              </>
            ) : (
              "Share"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

ShareModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  conversationId: PropTypes.string,
  conversationName: PropTypes.string,
};
