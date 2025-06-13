// NOTE: We don't have authentication, so this is just a placeholder UI
// You would need to add DropdownMenu components from shadcn if you want the menu
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar"
import { Button } from "@/src/components/ui/button"

export function UserNav() {
  return (
    <Avatar className="h-9 w-9">
        <AvatarImage src="/avatars/01.png" alt="@pauly" />
        <AvatarFallback>P</AvatarFallback>
    </Avatar>
  )
}