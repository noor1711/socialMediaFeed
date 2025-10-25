"use client";

import React, { useEffect, useState } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export default function LoginForm({ login }: { login: any }) {
  const [email, setEmail] = useState();
  const [password, setPassword] = useState();
  const [errors, setErrors] = useState({email: "", password: ""});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateFields = (fieldType: string) => {
    if (fieldType == "email" && !email || fieldType == "password" && !password) {
      setErrors({...errors, [fieldType]: `Please enter a valid ${fieldType}`})
    }
  }
  
  const onSubmit = async () => {
    setIsSubmitting(true);
    await login({email, password})
    setIsSubmitting(false);
  };

  return (
    <Card className="w-full m-auto mt-50 md:w-[350px]">
      <CardHeader>
        <CardTitle>Login</CardTitle>
        <CardDescription>Enter your credentials to access your account</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              onChange={(e: any) => setEmail(e?.target?.value)}
              aria-invalid={errors.email ? "true" : "false"}
              onBlur={() => validateFields("email")}
            />
            {!!errors.email && <p className="mt-1 text-sm text-red-500">{errors.email}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              onChange={(e: any) => setPassword(e?.target?.value)}
              aria-invalid={errors.password ? "true" : "false"}
              onBlur={() => validateFields("password")}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-500">{errors.password}</p>
            )}
          </div>
        </form>
      </CardContent>
      <CardFooter>
        <Button type="submit" className="w-full" disabled={isSubmitting} onClick={onSubmit}>
          {isSubmitting ? "Logging in..." : "Login"}
        </Button>
      </CardFooter>
    </Card>
  );
}
