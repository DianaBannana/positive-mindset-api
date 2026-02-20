# SalesEcho AI - Frontend

Next.js frontend application for SalesEcho AI, providing a professional dashboard for sales reps to manage meeting transcriptions and summaries.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Supabase Auth Helpers
- **Icons**: Lucide React
- **UI Components**: Custom components (Shadcn/ui style)

## Prerequisites

- Node.js 18+ and npm
- Supabase project with authentication configured
- FastAPI backend running on `http://localhost:8000`

## Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables**:
   Create a `.env.local` file in the `frontend/` directory:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── dashboard/          # Protected dashboard routes
│   ├── login/              # Login page
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home page (redirects to login)
├── components/             # React components
│   ├── ui/                # Reusable UI components
│   ├── Sidebar.tsx        # Dashboard sidebar navigation
│   └── MeetingTable.tsx   # Meetings table component
├── lib/                   # Utilities and helpers
│   ├── api.ts             # FastAPI client
│   ├── supabase.ts        # Supabase client helpers
│   └── utils.ts           # Utility functions
└── public/                # Static assets
```

## Features

### Authentication
- Supabase authentication integration
- Protected routes with middleware
- Login page with email/password
- Automatic session management

### Dashboard
- **My Meetings**: View all meetings for the logged-in user's organization
- **Organizations**: Admin-only page for organization management (placeholder)
- **Analytics**: Analytics dashboard (placeholder)

### Meeting Table
- Displays meetings with:
  - Date and time
  - Client name
  - Status badges (PENDING, PROCESSING, COMPLETED, FAILED)
  - Duration
  - View Summary button (enabled for completed meetings)

### Responsive Design
- Mobile-friendly sidebar with hamburger menu
- Responsive table layout
- Touch-friendly buttons and interactions

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`:

- `GET /api/v1/meetings?org_id={org_id}` - Fetch meetings for an organization
- `GET /api/v1/meetings/{meeting_id}` - Fetch a single meeting

See `lib/api.ts` for the API client implementation.

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Adding New Pages

1. Create a new file in `app/dashboard/` directory
2. Add a navigation item in `components/Sidebar.tsx`
3. The route will be automatically protected by middleware

### Styling

- Uses Tailwind CSS for styling
- Custom components follow Shadcn/ui patterns
- Responsive breakpoints: `sm:`, `md:`, `lg:`, `xl:`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `NEXT_PUBLIC_API_URL` | FastAPI backend URL | Yes (defaults to http://localhost:8000) |

## Notes

- The dashboard currently uses a placeholder `org_id` from user metadata. You'll need to:
  1. Store `org_id` in Supabase user metadata when creating users
  2. Or fetch it from a separate API endpoint
  3. Update `app/dashboard/page.tsx` to use the actual org_id

- The "View Summary" button currently navigates to a placeholder route. Implement the meeting detail page at `app/dashboard/meetings/[id]/page.tsx`

## Troubleshooting

### Authentication Issues
- Ensure Supabase credentials are correct in `.env.local`
- Check that Supabase authentication is enabled in your project
- Verify user exists in Supabase Auth

### API Connection Issues
- Ensure FastAPI backend is running on `http://localhost:8000`
- Check CORS settings in FastAPI backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly

### Build Issues
- Clear `.next` directory: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

## Next Steps

- [ ] Implement meeting detail page
- [ ] Add file upload functionality
- [ ] Implement organization management
- [ ] Add analytics dashboard
- [ ] Add user profile page
- [ ] Implement real-time updates with Supabase Realtime
