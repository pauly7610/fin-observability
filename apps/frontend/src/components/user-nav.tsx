'use client'

import { UserButton } from '@clerk/nextjs'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

const hasClerk = !!(
  typeof process !== 'undefined' &&
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
  !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.includes('placeholder')
)

export function UserNav() {
  if (hasClerk) {
    return <UserButton afterSignOutUrl="/sign-in" />
  }
  return (
    <Avatar className="h-8 w-8">
      <AvatarFallback className="bg-primary/10 text-primary text-xs">?</AvatarFallback>
    </Avatar>
  )
}
