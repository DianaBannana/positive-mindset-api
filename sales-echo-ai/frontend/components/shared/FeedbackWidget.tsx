"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown, Edit3, Check, X, Loader2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type FeedbackSectionType = 
  | "summary" 
  | "action_items" 
  | "deal_value" 
  | "next_meeting" 
  | "objection"
  | "contact_email";

export type FeedbackType = 
  | "accuracy" 
  | "missing" 
  | "hallucination" 
  | "incomplete" 
  | "wrong_language";

interface FeedbackWidgetProps {
  meetingId: string;
  orgId: string;
  sectionType: FeedbackSectionType;
  sectionIndex?: number;
  originalValue?: any;
  onFeedbackSubmitted?: (rating: string) => void;
  compact?: boolean;
  className?: string;
}

interface FeedbackState {
  rating: "positive" | "negative" | "neutral" | null;
  isEditing: boolean;
  correctedValue: string;
  feedbackNote: string;
  feedbackType: FeedbackType;
  isSubmitting: boolean;
  isSubmitted: boolean;
}

export function FeedbackWidget({
  meetingId,
  orgId,
  sectionType,
  sectionIndex,
  originalValue,
  onFeedbackSubmitted,
  compact = false,
  className,
}: FeedbackWidgetProps) {
  const [state, setState] = useState<FeedbackState>({
    rating: null,
    isEditing: false,
    correctedValue: "",
    feedbackNote: "",
    feedbackType: "accuracy",
    isSubmitting: false,
    isSubmitted: false,
  });

  const handleRating = async (rating: "positive" | "negative") => {
    // If clicking negative, show edit mode
    if (rating === "negative" && !state.isEditing) {
      setState(prev => ({
        ...prev,
        rating,
        isEditing: true,
        correctedValue: typeof originalValue === "string" ? originalValue : JSON.stringify(originalValue, null, 2),
      }));
      return;
    }

    // Submit positive rating directly
    if (rating === "positive") {
      await submitFeedback(rating, null, "");
    }
  };

  const submitFeedback = async (
    rating: "positive" | "negative",
    correctedValue: any,
    feedbackNote: string,
  ) => {
    setState(prev => ({ ...prev, isSubmitting: true }));

    try {
      const response = await fetch(`${API_URL}/api/v1/feedback?org_id=${orgId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          meeting_id: meetingId,
          section_type: sectionType,
          section_index: sectionIndex,
          rating,
          feedback_type: state.feedbackType,
          original_value: originalValue,
          corrected_value: correctedValue,
          feedback_note: feedbackNote,
          category_tags: detectCategoryTags(feedbackNote),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit feedback");
      }

      setState(prev => ({
        ...prev,
        rating,
        isEditing: false,
        isSubmitting: false,
        isSubmitted: true,
      }));

      onFeedbackSubmitted?.(rating);
    } catch (error) {
      console.error("Feedback submission error:", error);
      setState(prev => ({ ...prev, isSubmitting: false }));
    }
  };

  const handleSubmitCorrection = () => {
    let correctedValue: any = state.correctedValue;
    
    // Try to parse as JSON if it looks like JSON
    if (state.correctedValue.trim().startsWith("{") || state.correctedValue.trim().startsWith("[")) {
      try {
        correctedValue = JSON.parse(state.correctedValue);
      } catch {
        // Keep as string
      }
    }

    submitFeedback("negative", correctedValue, state.feedbackNote);
  };

  const handleCancel = () => {
    setState(prev => ({
      ...prev,
      rating: null,
      isEditing: false,
      correctedValue: "",
      feedbackNote: "",
    }));
  };

  // Auto-detect category tags from feedback note
  const detectCategoryTags = (note: string): string[] => {
    const tags: string[] = [];
    const lowerNote = note.toLowerCase();
    
    if (lowerNote.includes("objection") || lowerNote.includes("התנגדות")) {
      tags.push("technical_objection");
    }
    if (lowerNote.includes("budget") || lowerNote.includes("תקציב") || lowerNote.includes("price")) {
      tags.push("budget");
    }
    if (lowerNote.includes("timeline") || lowerNote.includes("deadline") || lowerNote.includes("זמן")) {
      tags.push("timeline");
    }
    if (lowerNote.includes("competitor") || lowerNote.includes("מתחרה")) {
      tags.push("competitor");
    }
    
    return tags;
  };

  if (state.isSubmitted) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Badge 
          variant="outline" 
          className={cn(
            "text-xs",
            state.rating === "positive" 
              ? "bg-emerald-50 text-emerald-700 border-emerald-200" 
              : "bg-amber-50 text-amber-700 border-amber-200"
          )}
        >
          <Check className="h-3 w-3 mr-1" />
          Feedback recorded
        </Badge>
      </div>
    );
  }

  if (state.isEditing) {
    return (
      <div className={cn("space-y-3 p-4 rounded-lg border border-amber-200 bg-amber-50", className)}>
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-amber-900">Help us improve</h4>
          <Button variant="ghost" size="icon" onClick={handleCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Feedback type selector */}
        <div className="flex flex-wrap gap-2">
          {(["accuracy", "missing", "hallucination", "incomplete"] as FeedbackType[]).map((type) => (
            <button
              key={type}
              onClick={() => setState(prev => ({ ...prev, feedbackType: type }))}
              className={cn(
                "px-2 py-1 text-xs rounded-full border transition-colors",
                state.feedbackType === type
                  ? "bg-amber-600 text-white border-amber-600"
                  : "bg-white text-amber-700 border-amber-300 hover:bg-amber-100"
              )}
            >
              {type === "accuracy" && "Inaccurate"}
              {type === "missing" && "Missing info"}
              {type === "hallucination" && "Not in transcript"}
              {type === "incomplete" && "Incomplete"}
            </button>
          ))}
        </div>

        {/* Correction textarea */}
        <div>
          <label className="text-xs text-amber-700 mb-1 block">
            Corrected version (optional)
          </label>
          <textarea
            value={state.correctedValue}
            onChange={(e) => setState(prev => ({ ...prev, correctedValue: e.target.value }))}
            className="w-full p-2 text-sm rounded border border-amber-200 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-amber-500"
            rows={3}
            placeholder="Enter the correct value..."
            dir="auto"
          />
        </div>

        {/* Feedback note */}
        <div>
          <label className="text-xs text-amber-700 mb-1 block">
            Additional notes
          </label>
          <textarea
            value={state.feedbackNote}
            onChange={(e) => setState(prev => ({ ...prev, feedbackNote: e.target.value }))}
            className="w-full p-2 text-sm rounded border border-amber-200 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-amber-500"
            rows={2}
            placeholder="What did the AI get wrong? (e.g., 'Missed the technical objection about API limits')"
            dir="auto"
          />
        </div>

        {/* Submit buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleSubmitCorrection}
            disabled={state.isSubmitting}
            size="sm"
            className="flex-1 bg-amber-600 hover:bg-amber-700"
          >
            {state.isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Check className="h-4 w-4 mr-2" />
            )}
            Submit Feedback
          </Button>
          <Button
            onClick={handleCancel}
            variant="outline"
            size="sm"
            className="border-amber-300"
          >
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  // Compact mode - just thumbs buttons
  if (compact) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <button
          onClick={() => handleRating("positive")}
          disabled={state.isSubmitting}
          className={cn(
            "p-1 rounded transition-colors",
            state.rating === "positive"
              ? "bg-emerald-100 text-emerald-600"
              : "text-gray-400 hover:text-emerald-600 hover:bg-emerald-50"
          )}
          title="Accurate"
        >
          <ThumbsUp className="h-4 w-4" />
        </button>
        <button
          onClick={() => handleRating("negative")}
          disabled={state.isSubmitting}
          className={cn(
            "p-1 rounded transition-colors",
            state.rating === "negative"
              ? "bg-red-100 text-red-600"
              : "text-gray-400 hover:text-red-600 hover:bg-red-50"
          )}
          title="Needs correction"
        >
          <ThumbsDown className="h-4 w-4" />
        </button>
      </div>
    );
  }

  // Full mode - with labels
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="text-xs text-gray-500">Rate accuracy:</span>
      <Button
        onClick={() => handleRating("positive")}
        disabled={state.isSubmitting}
        variant="ghost"
        size="sm"
        className={cn(
          "h-7 px-2",
          state.rating === "positive" && "bg-emerald-100 text-emerald-600"
        )}
      >
        <ThumbsUp className="h-3 w-3 mr-1" />
        Accurate
      </Button>
      <Button
        onClick={() => handleRating("negative")}
        disabled={state.isSubmitting}
        variant="ghost"
        size="sm"
        className={cn(
          "h-7 px-2",
          state.rating === "negative" && "bg-red-100 text-red-600"
        )}
      >
        <ThumbsDown className="h-3 w-3 mr-1" />
        Fix
      </Button>
    </div>
  );
}

// Feedback summary component for showing feedback status
interface FeedbackSummaryProps {
  meetingId: string;
  orgId: string;
  className?: string;
}

export function FeedbackSummary({ meetingId, orgId, className }: FeedbackSummaryProps) {
  const [feedback, setFeedback] = useState<{
    feedback_count: number;
    feedback: Array<{
      section_type: string;
      rating: string;
    }>;
  } | null>(null);

  // Fetch feedback on mount
  useState(() => {
    fetch(`${API_URL}/api/v1/feedback/meeting/${meetingId}?org_id=${orgId}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => setFeedback(data))
      .catch(() => null);
  });

  if (!feedback || feedback.feedback_count === 0) {
    return null;
  }

  const positive = feedback.feedback.filter(f => f.rating === "positive").length;
  const negative = feedback.feedback.filter(f => f.rating === "negative").length;

  return (
    <div className={cn("flex items-center gap-2 text-xs", className)}>
      <MessageSquare className="h-3 w-3 text-gray-400" />
      <span className="text-gray-500">Feedback:</span>
      {positive > 0 && (
        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
          <ThumbsUp className="h-2 w-2 mr-1" />
          {positive}
        </Badge>
      )}
      {negative > 0 && (
        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
          <ThumbsDown className="h-2 w-2 mr-1" />
          {negative}
        </Badge>
      )}
    </div>
  );
}
