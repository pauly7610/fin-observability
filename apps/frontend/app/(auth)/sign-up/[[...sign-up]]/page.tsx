import { SignUp } from '@clerk/nextjs'
import { redirect } from 'next/navigation'

const hasClerk = !!(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY &&
  !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.includes('placeholder')
)

export default function SignUpPage() {
  if (!hasClerk) redirect('/')
  return (
    <SignUp
      appearance={{
        elements: {
          rootBox: 'mx-auto',
        },
      }}
      afterSignUpUrl="/"
      signInUrl="/sign-in"
    />
  )
}
