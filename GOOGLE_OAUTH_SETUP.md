# Google Workspace OAuth Integration Setup Guide

This guide will help you set up Google Workspace OAuth integration for your Agentic CRM system, enabling login with Google accounts and access to Gmail, Calendar, and Drive APIs.

## Prerequisites

- Google Cloud Platform account
- Your Agentic CRM system running locally or deployed

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `Agentic CRM Integration`
4. Click "Create"

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable the following APIs:
   - **Google+ API** (for user info)
   - **Gmail API** (for email integration)
   - **Google Calendar API** (for calendar integration)
   - **Google Drive API** (for file storage)

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type (unless you have Google Workspace)
3. Fill in required information:
   - **App name**: `Agentic CRM`
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Add scopes:
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `../auth/gmail.readonly`
   - `../auth/gmail.send`
   - `../auth/calendar.readonly`
   - `../auth/calendar.events`
   - `../auth/drive.readonly`
   - `../auth/drive.file`
5. Add test users (your email addresses)
6. Save and continue

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set name: `Agentic CRM Web Client`
5. Add authorized origins:
   - `http://localhost:5001` (your backend)
   - `http://localhost:8080` (your frontend)
   - Add your production domains if deployed
6. Add authorized redirect URIs:
   - `http://localhost:5001/api/auth/google/callback`
   - Add your production callback URL if deployed
7. Click "Create"
8. **Save the Client ID and Client Secret** - you'll need these!

## Step 5: Set Environment Variables

Add these environment variables to your system:

### For Development (add to your shell profile)

```bash
export GOOGLE_CLIENT_ID="your-client-id-here.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret-here"
```

### For Production

Set these in your deployment environment (Heroku, Docker, etc.)

## Step 6: Restart Your Backend Server

After setting the environment variables:

```bash
# Stop the current backend server (Ctrl+C)
cd /Users/ryanwalker/CascadeProjects/agentic-crm/backend
PORT=5001 python3 run.py
```

## Step 7: Test Google OAuth

1. Open your CRM at `http://localhost:8080`
2. Click "Continue with Google Workspace"
3. You should be redirected to Google's OAuth consent screen
4. Grant permissions
5. You should be redirected back and logged in

## Troubleshooting

### Common Issues

1. **"OAuth not configured" error**
   - Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
   - Restart your backend server after setting variables

2. **"Redirect URI mismatch" error**
   - Check that your redirect URI in Google Console matches exactly
   - Make sure you're using the correct port (5001 for backend)

3. **"Access blocked" error**
   - Add your email to test users in OAuth consent screen
   - Make sure all required APIs are enabled

4. **"Invalid client" error**
   - Double-check your Client ID and Secret
   - Make sure they're set as environment variables correctly

### Verify Setup

Check if OAuth is configured by visiting:
`http://localhost:5001/api/auth/google/status`

This should return:

```json
{
  "configured": true,
  "client_id_set": true,
  "client_secret_set": true,
  "scopes": [...],
  "setup_url": "https://console.cloud.google.com/"
}
```

## Security Notes

- Never commit your Client ID and Secret to version control
- Use environment variables for all credentials
- In production, use HTTPS for all OAuth flows
- Regularly rotate your OAuth credentials
- Monitor API usage in Google Cloud Console

## What You Get After Setup

Once configured, your CRM will have:

1. **Google Login** - Users can sign in with their Google accounts
2. **Gmail Integration** - Read and send emails through the CRM
3. **Calendar Integration** - View and create calendar events
4. **Drive Integration** - Access and store files
5. **Automatic User Creation** - New users created from Google accounts
6. **Secure Token Management** - OAuth tokens stored securely

## Need Help?

If you encounter issues:

1. Check the browser console for errors
2. Check your backend server logs
3. Verify all environment variables are set
4. Ensure all APIs are enabled in Google Cloud Console
5. Make sure redirect URIs match exactly

Your Agentic CRM system is now ready for Google Workspace integration!
