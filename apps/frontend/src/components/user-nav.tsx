// NOTE: We don't have authentication, so this is just a placeholder UI
// You would need to add DropdownMenu components from shadcn if you want the menu
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

export function UserNav() {
  return (
    <Avatar className="h-8 w-8">
      <AvatarImage src="/avatars/01.png" alt="@pauly" />
      <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
        P
      </AvatarFallback>
    </Avatar>
  )
}