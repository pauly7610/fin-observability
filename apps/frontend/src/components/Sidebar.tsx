'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useTheme } from 'next-themes'
import {
  LayoutDashboard,
  AlertTriangle,
  Shield,
  Bot,
  Brain,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
  Activity,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'
import { useState } from 'react'
import { UserNav } from '@/components/user-nav'

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/incidents', label: 'Incidents', icon: AlertTriangle },
  { href: '/compliance', label: 'Compliance', icon: Shield },
  { href: '/agent', label: 'Agent', icon: Bot },
  { href: '/explainability', label: 'Explainability', icon: Brain },
]

export function Sidebar() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'flex flex-col h-screen border-r border-border bg-card transition-all duration-200 ease-in-out',
          collapsed ? 'w-[68px]' : 'w-[240px]'
        )}
      >
        {/* Logo / Brand */}
        <div className={cn(
          'flex items-center h-14 px-4 border-b border-border',
          collapsed ? 'justify-center' : 'gap-3'
        )}>
          <Activity className="h-6 w-6 text-primary shrink-0" />
          {!collapsed && (
            <span className="text-sm font-bold tracking-tight truncate">
              FinAI Observability
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = item.href === '/'
              ? pathname === '/'
              : pathname.startsWith(item.href)
            const Icon = item.icon

            const linkContent = (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                  collapsed && 'justify-center px-2'
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            )

            if (collapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent side="right" className="font-medium">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              )
            }

            return linkContent
          })}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-border p-2 space-y-1">
          {/* Theme toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? 'icon' : 'sm'}
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className={cn(
                  'w-full text-muted-foreground hover:text-foreground',
                  !collapsed && 'justify-start gap-3 px-3'
                )}
              >
                <Sun className="h-4 w-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
                {!collapsed && <span className="text-sm">Toggle theme</span>}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">Toggle theme</TooltipContent>
            )}
          </Tooltip>

          {/* Collapse toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? 'icon' : 'sm'}
                onClick={() => setCollapsed(!collapsed)}
                className={cn(
                  'w-full text-muted-foreground hover:text-foreground',
                  !collapsed && 'justify-start gap-3 px-3'
                )}
              >
                {collapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <>
                    <ChevronLeft className="h-4 w-4" />
                    <span className="text-sm">Collapse</span>
                  </>
                )}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            )}
          </Tooltip>

          {/* User */}
          <div className={cn(
            'flex items-center pt-2',
            collapsed ? 'justify-center' : 'gap-3 px-3'
          )}>
            <UserNav />
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">Admin</p>
                <p className="text-xs text-muted-foreground truncate">admin@example.com</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </TooltipProvider>
  )
}
