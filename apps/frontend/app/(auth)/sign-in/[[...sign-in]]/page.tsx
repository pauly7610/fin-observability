import { SignIn } from '@clerk/nextjs'
import { redirect } from 'next/navigation'

const hasClerk = !!(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
  !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.includes('placeholder')
)

export default function SignInPage() {
  if (!hasClerk) redirect('/')
  return (
    <SignIn
      appearance={{
        elements: {
          rootBox: 'mx-auto',
        },
      }}
      afterSignInUrl="/"
      signUpUrl="/sign-up"
    />
  )
}
